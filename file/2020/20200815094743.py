from bs4 import BeautifulSoup
import threading, time, requests, os, urllib3
from requests.adapters import HTTPAdapter
# 忽略request 警告
requests.packages.urllib3.disable_warnings()


def mkdir(path):
    folder = os.path.exists(path)
    if not folder:
        d = os.makedirs(path)
    return path

 
   
class StoppableThread(threading.Thread):
    """封装stop和stoped的thread """

    def __init__(self,  *args, **kwargs):
        super(StoppableThread, self).__init__(*args, **kwargs)
        self._stop_event = threading.Event()

    def stop(self):
        self._stop_event.set()

    def stopped(self):
        return self._stop_event.is_set()

class Spider():
    '''  正文  '''
    headers = {
        'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) '
                      'Chrome/65.0.3325.181 Safari/537.36',
        'Referer': "https://www.naixue.org/"
    } 

    spider_url = 'https://www.naixue.org'
    s = requests.session()
    # 网络错误重连3次
    s.mount('https://www.naixue.org/', HTTPAdapter(max_retries=3))
    s.keep_alive = False


    def __init__(self, itype='tuwanyinghua', pages=28): 
        self.itype = itype
        self.pages = pages 



    def creat_soup(self, url):
        '''
        该函数返回一个url的soup对象
        :param url:一个页面的链接
        '''
        # 获取网页，得到一个response对象
        try:
            response = self.s.get(url, headers=self.headers, verify=False, timeout=30)
        except requests.exceptions.RequestException as e:
            print(e)
        # 指定自定义编码，让文本按指定的编码进行解码，因为网站的charset = gb2312
        # response.encoding = 'gb2312' 
        return BeautifulSoup(response.text, 'html.parser')
    

    def get_url(self): 
        url_list = []
        try:
            for i in range(1, self.pages+1):
                # page=s.get(self.spider_url +"/"+self.itype+"/page_"+str(i)+'.html',headers=self.headers, verify=False).text
                soup = self.creat_soup(self.spider_url +"/"+self.itype+"/page_"+str(i)+'.html')
                url_div = soup.findAll("div", {"class": "update_area_content"})[0]
                page_base_url = url_div.find_all("li")
                for page_url in page_base_url: 
                    url = page_url.find("a").get("href") 
                    url_list.append(url)
                i = i+1 
            return url_list
        except Exception as e:
            pass
        finally:
            return url_list
            
    
    def get_singe_urls(self, turl):
        page_url = [turl]
        base_url = turl.replace('.html', '')
        # p = s.get(url ,headers=self.headers, verify=False).text
        # soup = BeautifulSoup(p, "html.parser") 
        soup = self.creat_soup(turl)
        try:
            s_pages = soup.find("div", {"class": "page_imges"}).findAll('a')
            del s_pages[0] 
            del s_pages[-1]
            lastPage = s_pages[-1].text.strip()
            total = int(lastPage) 
        except Exception as e:
            print(e)
            total = 1
        page_url2 = [ (base_url+'_'+str(i))+'.html' for i in range(1, (total+1)) if i!=1 ]
        return page_url+page_url2
    
    def get_img_list(self, urls):
        img_list = [] 
        for url in urls: 
            # p = s.get(url ,headers=self.headers, verify=False).text
            # soup = BeautifulSoup(p, "html.parser") 
            soup = self.creat_soup(url)
            x = soup.findAll("div", {"class": "image_div"})
            d = x[0].findAll('img')
            # title = select('h1.article-title')[0].text.strip()
            title = soup.findAll('div', {'class':'item_title'})[0].select('h1')[0].text.strip()
            for i in d:
                t = i.get('src')
                imgUrl = t.split('?')
                img_list.append(imgUrl[0])
        return {'title':title, 'imgs':img_list}

    
    def get_single_imgs(self, url):
        all_urls = self.get_singe_urls(url)
        imglist  = self.get_img_list(all_urls)
        return imglist

    def saveImgs(self, title, imgs):
        img_list = {
            'title':title,
            'imgs':imgs
        }
        imgPath = os.path.abspath('./')+'\\'+self.itype+'\\'
        folder = mkdir(imgPath+img_list['title'])
        print('开始下载:'+img_list['title']+',共计图片:'+str(len(img_list['imgs'])) +'张')
        count = 1
        namelist = []
        for index,img in enumerate(img_list['imgs']):
            try:
                html = self.s.get(img, headers=self.headers, timeout=30)
                filename=folder+'\\'+str(index + 1)+'.jpg'
                # print('正在下载第{count}张图片.'.format(count=count))
                with open(filename, 'wb') as handle:
                    handle.write(html.content)
                count += 1
            except Exception as e:
                print(e)
                continue
        print('Finisded! '+img_list['title']+'结束,共计下载'+str(count)+'张图片')


    def downTask(self):
        
        allUrls = self.get_url()
        # print(allUrls)
        thread_list = []
        totalTask = len(allUrls)
        count = 1
        for url in allUrls: 
            imgs_lists = self.get_single_imgs(url) 
            count +=1
            # self.saveImgs(imgs_lists)
            try:
                th = StoppableThread(target=self.saveImgs, args=(imgs_lists['title'], imgs_lists['imgs'])) 
                th.start() 
                thread_list.append(th)
            except (KeyboardInterrupt, SystemExit):
                th.stop()
                sys.exit() 
        for x in thread_list:
            x.join()

    def run(self):
        print("程序于 {} 开始启动，请等待...".format(time.ctime()))
        self.downTask()  

if __name__ == '__main__':
    spider = Spider(itype='beautyleg', pages=82)
    # 选定一个分类爬取，如果大佬想一劳永逸：
    # 定义一个分类列表 typeList= ['beautyleg', 'tuwanyinghua'......]， 然后遍历
    spider.run()
 

