# -*- coding: utf-8 -*-

import requests
import urllib
import json
from tqdm import tqdm

# User config
zxw_user = 'your username'
zxw_pwd = 'your password'

common_headers = {
    'Accept': 'application/json, text/plain, */*',
    'User-Agent': 'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.163 Safari/537.36',
    'Origin': 'https://www.zhixue.com',
    'Referer': 'https://www.zhixue.com/middleweb/student',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'zh-CN,zh;q=0.9'
}
cas_url = 'https://sso.zhixue.com/sso_alpha/'
service_url = 'https://www.zhixue.com:443/ssoservice.jsp'
list_url = 'https://www.zhixue.com/middleweb/homework_middle_service/stuapp/getStudentHomeWorkList?subjectCode=-1&completeStatus=-1&pageSize=20&pageIndex='
api_url = 'https://www.zhixue.com/middleweb/homework_middle_service/stuapp/newGetHomeworkDetail'

if __name__ == '__main__':
    session = requests.session()
    session.mount('https://', requests.adapters.HTTPAdapter(max_retries=5))
    sso_res = session.get(cas_url + '/login?service=' + urllib.parse.quote(service_url), headers=common_headers).text.strip()
    sso_res = json.loads(sso_res[2:-2].replace('\\', ''))
    if sso_res['result'] != 'success':
        print(sso_res['message'])
        exit(1)
    sso_params = urllib.parse.urlencode({
        'service': service_url,
        'encode': 'false',
        'sourceappname': 'tkyh,tkyh',
        '_eventId': 'submit',
        'appId': 'zx-container-client',
        'client': 'web',
        'type': 'loginByNormal',
        'key': 'auto',
        'lt': sso_res['data']['lt'],
        'execution': sso_res['data']['execution'],
        'customLogoutUrl': 'https://www.zhixue.com/login.html',
        'ncetAppId': 'QLIqXrxyxFsURfFhp4Hmeyh09v6aYTq1',
        'sysCode': '',
        'username': zxw_user,
        'password': zxw_pwd
    })
    sso_res = session.get(cas_url + '/login?' + sso_params, headers=common_headers).text.strip()
    sso_res = json.loads(sso_res[2:-2].replace('\\', ''))
    if sso_res['result'] != 'success':
        print(sso_res['message'])
        exit(1)
    session.post(service_url, {
        'action': 'login',
        'ticket': sso_res['data']['st']
    }, headers=common_headers)
    problem_list = session.get(list_url + '1', headers=common_headers).text
    problem_list = json.loads(problem_list)
    if problem_list['code'] != 200:
        print(problem_list['info'])
        exit(1)
    idx = 0
    for item in problem_list['result']['list']:
        idx += 1
        print('%2d: (%s) %s' % (idx, item['subjectName'], item['hwTitle']))
    page = 1
    print('当前查看第 %d 页的项目' % page)
    while True:
        read = input('\n > [1~20]选择/[+]下一页/[-]上一页/[其余]退出\n > ').strip()
        if not read.isdigit():
            if read == '+':
                page += 1
                problem_list = session.get(list_url + str(page), headers=common_headers).text
                problem_list = json.loads(problem_list)
                if problem_list['code'] != 200:
                    print(problem_list['info'])
                    exit(1)
                idx = 0
                for item in problem_list['result']['list']:
                    idx += 1
                    print('%2d: (%s) %s' % (idx, item['subjectName'], item['hwTitle']))
                print('当前查看第 %d 页的项目' % page)
            elif read == '-':
                if page == 1:
                    print('笨比，这就是第一页，前面没东西')
                    continue
                page -= 1
                problem_list = session.get(list_url + str(page), headers=common_headers).text
                problem_list = json.loads(problem_list)
                if problem_list['code'] != 200:
                    print(problem_list['info'])
                    exit(1)
                idx = 0
                for item in problem_list['result']['list']:
                    idx += 1
                    print('%2d: (%s) %s' % (idx, item['subjectName'], item['hwTitle']))
                print('当前查看第 %d 页的项目' % page)
            else:
                exit(0)
            continue
        idx = int(read) - 1
        if not(idx in range(20)):
            exit(0)
        info = session.post(api_url, {
            'hwId': problem_list['result']['list'][idx]['hwId'],
            'stuHwId': problem_list['result']['list'][idx]['stuHwId']
        }, headers=common_headers).text
        info = json.loads(info)
        if info['code'] != 200:
            print(info['info'])
            print('可能是 Cookie 失效或其他原因，请稍后重试。')
            exit(1)
        res = info['result']
        if res['hwType'] != 3:
            print(' [!] 暂不支持的作业类型(hwType = %d)，结果无法预期' % res['hwType'])
        print('读取到 %d 个题目文件：' % len(res['quesResList']))
        idx = 0
        for item in res['quesResList']:
            idx += 1
            print(' P%d: (%s) %s' % (idx, item['fileType'], item['resourceName']))
        print('读取到 %d 个答案文件：' % len(res['ansResList']))
        idx = 0
        for item in res['ansResList']:
            idx += 1
            print(' A%d: (%s) %s' % (idx, item['fileType'], item['resourceName']))
        while True:
            read = input('\n > [Pn/An]下载对应文件/[S(can)]扫描答案/[其余]返回题目列表(不区分大小写)\n > ').strip().lower()
            if len(read) > 1 and (read[0] == 'p' or read[0] == 'a'):
                idx = read[1:]
                if not idx.isdigit():
                    break
                idx = int(idx) - 1
                if read[0] == 'p':
                    target = res['quesResList']
                else:
                    target = res['ansResList']
                if not(idx in range(len(target))):
                    break
                with open(target[idx]['resourceName'], 'wb') as f:
                    with session.get(target[idx]['resourcePath'], headers=common_headers, stream=True) as r:
                        file_size = int(r.headers['Content-Length'])
                        chunk_size = 128
                        with tqdm(total=file_size) as pbar:
                            for chunk in r.iter_content(chunk_size):
                                f.write(chunk)
                                pbar.update(len(chunk))
            elif read == 's' or read == 'scan':
                for item in res['mainList']:
                    print(item['sortTitle'])
                    if item['type'] == '02':
                        print(' [!] 拍照上传题型，扫描结果仅供参考，可能为空')
                        for option in item['optionList']:
                            if option['answer'].strip() == '':
                                continue
                            print('%s. %s' % (option['displayName'], option['answer'].strip()))
                    elif item['type'] == '03':
                        for option in item['optionList']:
                            print('%s.%s' % (option['displayName'], option['answer']), end=' ')
                        print('')
                    elif item['type'] == '04':
                        print(' [!] 自动批改填空题型，每组答案换行，可能含有 LaTeX 公式，仅供参考')
                        for option in item['optionList']:
                            print('%s. ' % option['displayName'], end='')
                            if option['answer'] == None or option['answer'].strip() == '':
                                print('')
                                continue
                            answers = json.loads(option['answer'])[0]
                            idx = 0
                            for answer in answers['blankAnswerList']:
                                if idx > 0:
                                    print(' (或) ', end='')
                                print(answer, end='')
                                idx += 1
                            print('')
                    else:
                        print(' [!] 尚未入库(type = %s)，不予扫描' % item['type'])
            else:
                break
