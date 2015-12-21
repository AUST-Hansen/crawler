# coding:utf8
from math import sqrt
from util import get_days, get_files, connect

host = '54.223.178.198'
start_time = '15-11-01'
end_time = '15-11-06'
gaps = range(1, 25)
path = '/home/cy/tmp/pm/'
day_gaps=range(1,10)

def map_line(x):
    """从文件的每一行读取有用信息"""
    res = x.split('  ')
    r0 = eval(res[0].split(' ')[-1])[1]
    # 不需要取全部240个小时只要 需要的即可
    max_t=max(gaps)
    max_t=max_t if max_t>28 else 28
    max_t=240
    r = [eval(ii)[1] for ii in res[1:max_t]]
    r.insert(0, r0)

    return [res[0].split(' ')[0], r]

def check(all_lines):
    '''
    简单的检查, 并不保证文件百分百正确, 但是出错概率极低
    :param all_lines:
    :return:
    '''
    if len(all_lines) != 1458: return False
    return all_lines[999].startswith('1475A ')

def calculate(all_data, gaps=[1], city=0):
    '''
   :param all_data: 所有的数据, 每一行代表着一个时间的数据,
   :param gaps: 所有要处理的间隔
   :param city: 监测站编号
   :return: 所有间隔(矩阵 2*len(gaps))
     '''
    results = [list(), list()]
    for gap in gaps:
        real_len = 0
        mae = mse = 0
        for ii in range(len(all_data) - gap):
            if all_data[ii] == -1 or all_data[ii + gap] == -1\
                    or all_data[ii].has_key(city)==False or all_data[ii + gap].has_key(city)==False:
                continue
            real_len += 1
            mae += abs(all_data[ii][city][gap] - all_data[ii + gap][city][0])
            mse += (all_data[ii][city][gap] - all_data[ii + gap][city][0]) ** 2
        if real_len==0:
            results[0].append(-1)
            results[1].append(-1)
        else:
            results[0].append(float(mae) / real_len)
            results[1].append(sqrt(float(mse) / real_len))
    return results

def calculate_level(all_data, gaps=[1], city=0):
    '''
    统计等级差出现的次数
   :param all_data: 所有的数据, 每一行代表着一个时间的数据,
   :param gaps: 所有要处理的间隔
   :param city: 监测站编号
   :return: 所有间隔(矩阵 2*len(gaps))
     '''

    results=[]
    for gap in gaps:
        real_len = 0
        tmp={};dist=[]
        for ii in range(len(all_data) - gap):
            if all_data[ii] == -1 or all_data[ii + gap] == -1\
                    or all_data[ii].has_key(city)==False or all_data[ii + gap].has_key(city)==False:
                continue
            real_len += 1
            dist.append(abs(all_data[ii][city][gap]/50 - all_data[ii + gap][city][0]/50))
        if len(dist)==0:
            tmp['-1']=1
            results.append(tmp)
            continue

        for ii in range(max(dist)+1):
            if dist.count(ii)>0:
                tmp[str(ii)]=float(dist.count(ii))/(real_len)
        results.append(tmp)
    return results

def calculate2(x, y):
    '''
    计算两个组数据的mae和mse,数据中缺失值用-1 表示
    :param x: 第一组数据
    :param y: 第二组
    :return:(mae,mse)
    '''
    f = filter(lambda x: (x[0] + 1) * (x[1] + 1) != 0, zip(x, y))
    mse = map(lambda x: (x[0] - x[1]) ** 2, f)
    mae = map(lambda x: abs(x[0] - x[1]), f)
    c = len(f)
    if c==0:
        return [-1,-1]
    mae = reduce(lambda a, b: a + b, mae)
    mse = reduce(lambda a, b: a + b, mse)
     
    return [float(mae) / c, sqrt(float(mse) / c)]



def get_sample(all_data):
    '''
    获取每晚八点预测的第二天的天气, 获取第二天24小时的实测数值
    :param all_data:
    :return:[ 第二天实测值,8点预测数值]
    '''
    # 每天实测值
    t1 = {}
    for city in city_ids:
        t1[city] = list()

    for time1 in all_data[24:]:
        if time1 == -1:
            for nouse in t1:
                t1[nouse].append(-1)
        else:
            for ii in time1:
                if t1.has_key(ii):
                    t1[ii].append(time1[ii][0])
    # 八点预测值
    t2 = {}
    for city in city_ids:
        t2[city] = list()
    for time1 in all_data[20:-24:24]:
        if time1 == -1:
            for ii in city_ids:
                t2[ii] += [-1 for i in range(24*9)]

        else:
            for city in time1:
                if t1.has_key(city):
                    t2[city] += time1[city][4:-20]
                else:t2[city] += [-1 for i in range(24*9)]
    return (t1, t2)


def map2(data):
    '''
    @Deprec 已过期, 整合到calculate_level中 更省内存
    将aqi除以50+1得到等级
    :param data:
    :return:
    '''
    r = [];
    for time in data:
        if time == -1:
            r.append(-1)
            continue
        tmp = {}
        for city in time:
            tmp[city] = map(lambda x: x / 50 + 1, time[city])
        r.append(tmp)
    return r


def write2db(db, results, start_time, end_time, city_id):
    c = db.compare_results
    c.insert_one({
        'city': city_id,
        'data': results,
        'key': 'compare_results',
        'start_time': start_time,
        'end_time': end_time,
        'info': u'储存某一个城市的mse和mae'
    })


def process_file(file):
    f = open(path + file)
    all_lines = f.readlines()
    # 按照cityid排序
    all_lines = sorted(all_lines, lambda x, y: -cmp(x.split(' ')[0], y.split(' ')[0]))
    hour_info = map(map_line, all_lines)
    new_hour_info = {}
    for ii in hour_info:
        new_hour_info[ii[0]] = ii[1]
    f.close()
    return new_hour_info


if __name__ == '__main__':
    all_data = []
    files = get_files(start_time, end_time)
    for file in files:
        try:
            new_hour_info=process_file(file)
            print 'process file %s ' %file
            all_data.append(new_hour_info)
        except Exception as e:
            print e
            all_data.append(-1)
        finally:
            pass
    #   清空旧的计算结果
    print 'process file done'
    db = connect(host)
    c = db.compare_results
    c.delete_many({'key': 'compare_results'})
    city_ids=[ii['code'] for ii in db.stations.find()]
    t_24 = get_sample(all_data)#每晚八点预测的结果
    for ii in city_ids:
        print ii
        results = calculate(all_data, gaps, ii)#计算mae和mse
        tmp_r=[list(),list()]
        for gap in day_gaps:
            t8_gap=[]
            for kk in range((gap-1)*24,len(t_24[1][ii]),24*9):t8_gap+=(t_24[1][ii][kk:kk+24])
            results_24 = calculate2(t_24[0][ii][(gap-1)*24:], t8_gap)#计算每晚八点预测的第二天的mae和mse
            tmp_r[0].append(results_24[0])
            tmp_r[1].append(results_24[1])
        results.append( tmp_r)
        result_level = calculate_level(all_data, gaps, ii)#计算基于等级的mae和mse
        results.append( result_level)
        write2db(db, results, start_time, end_time, ii)
