from django.shortcuts import render
from django.http import HttpResponse, HttpResponseNotFound
from .forms import frm
from bs4 import BeautifulSoup as bs
import requests
import codecs,string

all_js = {
        "7540.b7f3ab16c1d7d344980b.js",
        "4826.ea570b7100e8c5e53e11.js",
        "Auth.44e05080311528b179c7.js",
        "MarkComplete.e9560adcebc4ad54e6bf.js",
        "UserActions.30ee83ef27eafec0be61.js",
        "Misc.a66f8a686e276f997313.js"
}
    
def index(request):
    
    context = {
        "title": "title",
        "mp": {1: "1", 2: "2"}
    }
    
    return render(request, 'index.html', context=context)

def scan(request):
    
    if (request.method != "POST"):
        return HttpResponseNotFound("only post requests accepted")
    
    urls_list = request.POST['urls'].split()
    
    res = {}
    for e in range(len(urls_list)):
        url = urls_list[e].strip()
        if url: 
            tt = process(url)
            res[url] = tt
        
    context = {
        "res": res,
    }
    
    return render(request, 'scan.html', context=context)

def ignore_c(c):
    return c==' ' or c.isdigit()

def hindi_percentage(str):
    
    is_hindi = 0
    
    for c in str:        
        maxchar = max(c)
        if ignore_c(c) or (u'\u0900' <= maxchar <= u'\u097f'):
            is_hindi += 1
    
    ret = is_hindi/len(str)
    
    return ret

def get_page(url):
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
    return response.text

def get_js_file(url):
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload, timeout=10)
    return response.status_code==200
    
def check_js_files(url, js_files):
    
    if url.endswith("index.html"):
        url = url[0: -len('index.html')]
    
    if not url.endswith("/"):
        url += '/'
    
    url += "webpack/"
    
    for fl in js_files:
        try:
            if not get_js_file(url + fl):
                return False
        except:
            return False
    
    return True

def process_body(body):
    
    cnt = 0
    cnt_script = 0
    pre_script = "<script"
    suf_script = "</script>"
    cnt_style = 0
    pre_style = "<style"
    suf_style = "</style>"

    res = []
    translated_cnt = 1
    words_cnt = 1
    
    for e in [e.strip() for e in body.prettify(formatter="html").split('\n')]:
        
        if len(e)==0:
            continue
        if e.startswith('<'): 
            cnt += 1
        if e.startswith(pre_script):
            cnt_script += 1
        if e==suf_script:
            cnt_script -= 1
        if e.startswith(pre_style):
            cnt_style += 1
        if e==suf_style:
            cnt_style -= 1

        good = True
        if cnt!=0 or cnt_script!=0 or cnt_style!=0 or e.endswith('>'):
            good = False
        
        if e.endswith('>'):
            cnt -= 1
        
        if good:
            res.append(e)
    
    for i in range(len(res)):
        text = bs(res[i], "html.parser").string
        if hindi_percentage(text) > 0.8:
            translated_cnt += 1
        words_cnt += 1
    
    return translated_cnt/words_cnt

def check_title(data):
    try:
        return hindi_percentage(data.title.string) >= 0.8
    except:
        return "title not found"

def process(url):
    
    print("PROCESSING: ", url)
    
    res_text = ''
    
    try:
        res_text = get_page(url)
    except:
        return {
            "success" : False,
            "error": "couldn't request the page"
        }
    
    data = bs(res_text, "html.parser")
    translated_percentage = process_body(data.body)
    
    return{
        "success" : True,
        "error": "",
        "translation_percentage" : translated_percentage,
        "title_is_translated" : check_title(data),
        "body_translated_pass" : translated_percentage > 0.85,
        "high_res_images": check_js_files(url, ["7540.b7f3ab16c1d7d344980b.js"]),
        "drop_down_menues": check_js_files(url, ["7540.b7f3ab16c1d7d344980b.js"]),
        "all_required_js_files": check_js_files(url, all_js),
    }