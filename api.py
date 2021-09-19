import requests
URL = 'https://kr.whatismymmr.com/api/v1/summoner?name='

def Rank(search='hide on bush'):
    try:
        Read_Json = requests.get(f"{URL}{search}").json()
        print(Read_Json)
        if 'error' in Read_Json:
            if Read_Json['error']['code'] == 0:
                return '예기치 않은 내부 서버 오류입니다.', None
            elif Read_Json['error']['code'] == 1:
                return '데이터베이스에 연결할 수 없습니다.', None
            elif Read_Json['error']['code'] == 100:
                return '소환사는 기록에 없습니다.', None
            elif Read_Json['error']['code'] == 101:
                return '소환사에 대한 최근 MMR 데이터가 없습니다.', None
            elif Read_Json['error']['code'] == 200:
                return '"이름" 쿼리 매개변수가 없습니다.', None
            elif Read_Json['error']['code'] == 9001:
                return '요청이 너무 많습니다.', None
                    
        _avg = Read_Json['ranked']['avg']
        _err = Read_Json['ranked']['err']
        _warn = Read_Json['ranked']['warn']
        _closestRank = Read_Json['ranked']['closestRank']
        _percentile = Read_Json['ranked']['percentile']
        if _avg == None:
            print(_avg, _err, _warn, _closestRank, _percentile)
            return '데이터가 충분하지 않습니다.', None
        if _percentile < 50:
                _percentile = '하위 ' + str(_percentile)
        else:
            _percentile = '상위 ' + str(_percentile)
        print(_avg, _err, _warn, _closestRank, _percentile)
        return f'[MMR]\n{_avg}±{_err}\n\n{_closestRank}의 {_percentile}%의 소환사들과 비슷합니다.', f'{_avg}±{_err}'
    except:
        return '잠시 후 다시시도 해주세요.\n문제가 계속 된다면 문의 바랍니다.', None

def Normal(search='hide on bush'):
    try:
        Read_Json = requests.get(f"{URL}{search}").json()
        print(Read_Json)
        if 'error' in Read_Json:
            if Read_Json['error']['code'] == 0:
                return '예기치 않은 내부 서버 오류입니다.', None
            elif Read_Json['error']['code'] == 1:
                return '데이터베이스에 연결할 수 없습니다.', None
            elif Read_Json['error']['code'] == 100:
                return '소환사는 기록에 없습니다.', None
            elif Read_Json['error']['code'] == 101:
                return '소환사에 대한 최근 MMR 데이터가 없습니다.', None
            elif Read_Json['error']['code'] == 200:
                return '"이름" 쿼리 매개변수가 없습니다.', None
            elif Read_Json['error']['code'] == 9001:
                return '요청이 너무 많습니다.', None

        _avg = Read_Json['normal']['avg']
        _err = Read_Json['normal']['err']
        _warn = Read_Json['normal']['warn']
        _closestRank = Read_Json['normal']['closestRank']
        _percentile = Read_Json['normal']['percentile']
        if _avg == None:
            print(_avg, _err, _warn, _closestRank, _percentile)
            return '데이터가 충분하지 않습니다.', None
        if _percentile < 50:
                _percentile = '하위 ' + str(_percentile)
        else:
            _percentile = '상위 ' + str(_percentile)
        print(_avg, _err, _warn, _closestRank, _percentile)
        return f'[MMR]\n{_avg}±{_err}\n\n{_closestRank}의 {_percentile}%의 소환사들과 비슷합니다.', f'{_avg}±{_err}'
    except:
        return '잠시 후 다시시도 해주세요.\n문제가 계속 된다면 문의 바랍니다.', None

def ARAM(search='hide on bush'):
    try:
        Read_Json = requests.get(f"{URL}{search}").json()
        print(Read_Json)
        if 'error' in Read_Json:
            if Read_Json['error']['code'] == 0:
                return '예기치 않은 내부 서버 오류입니다.', None
            elif Read_Json['error']['code'] == 1:
                return '데이터베이스에 연결할 수 없습니다.', None
            elif Read_Json['error']['code'] == 100:
                return '소환사는 기록에 없습니다.', None
            elif Read_Json['error']['code'] == 101:
                return '소환사에 대한 최근 MMR 데이터가 없습니다.', None
            elif Read_Json['error']['code'] == 200:
                return '"이름" 쿼리 매개변수가 없습니다.', None
            elif Read_Json['error']['code'] == 9001:
                return '요청이 너무 많습니다.', None
                
        _avg = Read_Json['ARAM']['avg']
        _err = Read_Json['ARAM']['err']
        _warn = Read_Json['ARAM']['warn']
        _closestRank = Read_Json['ARAM']['closestRank']
        _percentile = Read_Json['ARAM']['percentile']
        if _avg == None:
            print(_avg, _err, _warn, _closestRank, _percentile)
            return '데이터가 충분하지 않습니다.', None
        if _percentile < 50:
                _percentile = '하위 ' + str(_percentile)
        else:
            _percentile = '상위 ' + str(_percentile)
        print(_avg, _err, _warn, _closestRank, _percentile)
        return f'[MMR]\n{_avg}±{_err}\n\n{_closestRank}의 {_percentile}%의 소환사들과 비슷합니다.', f'{_avg}±{_err}'
    except:
        return '잠시 후 다시시도 해주세요.\n문제가 계속 된다면 문의 바랍니다.', None
