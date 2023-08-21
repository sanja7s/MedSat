import wasdi

def run():
    wasdi.setVerbose(True)

    calculateSizeOfSearch()
    
    
def calculateSizeOfSearch():
    asSizes = []
    aoIntervals = defineIntervals()
    print(f'will do {len(aoIntervals)} searches')
    for aoInterval in aoIntervals:
        aoResults = wasdi.searchEOImages(
            sPlatform="S2",
            sDateFrom=aoInterval['sDateFrom'],
            sDateTo=aoInterval['sDateTo'],
            sProductType="S2MSI2A",
            oBoundingBox={
                "northEast": {
                    "lat": 55.82,
                    "lng": 1.8
                },
                "southWest": {
                    "lat": 49.8,
                    "lng": -6.5
                }
            },
            sProvider="SENTINEL"
        )
        fSize = calcTotalSize(aoResults)
        sSizeLine = f'{aoInterval["sDateFrom"]}\t{aoInterval["sDateTo"]}\t{fSize}'
        asSizes.append(sSizeLine)

    print('size calculation done')
    print(asSizes)
    print('over')


def defineIntervals():
    # define intervals
    aoIntervals = [
        {
            "sDateFrom": "2018-12-01",
            "sDateTo": "2018-12-31"
        }
    ]
    for iM in range(1, 13):
        if(iM < 10):
            iM = f'0{iM}'
        aoIntervals.append({
            "sDateFrom": f"2019-{iM}-01",
            "sDateTo": f"2019-{iM}-31"
        })
    for iM in range(1, 13):
        if (iM < 10):
            iM = f'0{iM}'
        aoIntervals.append(
            {
                "sDateFrom": f"2020-{iM}-01",
                "sDateTo": f"2020-{iM}-31"
            }
        )
    aoIntervals.append(
        {
            "sDateFrom": f"2021-01-01",
            "sDateTo": f"2021-01-31"
        }
    )
    return aoIntervals
    
def calcTotalSize(aoProductList):
    fSize = 0.0
    for aoProduct in aoProductList:
        fSize += getLongSize(aoProduct)
    return fSize

def getLongSize(aoProduct):
    sSizeString, sSizeFormat = None, None
    try:
        sSizeString, sSizeFormat = aoProduct['properties']['size'].split(' ')
    except Exception as oE:
        print(f'ERROR!!!!!!!!!!!!!! {type(oE)}: {oE}')
        sSizeString, sSizeFormat = None, None

    if sSizeString is not None:
        fVal = float(sSizeString)
        if sSizeFormat is None or sSizeFormat=='' or sSizeFormat=='B':
            # assume bytes
            return fVal
        elif sSizeFormat.upper() == 'KB':
            return getBFromKB(fVal)
        elif sSizeFormat.upper() == 'MB':
            return getBfromMB(fVal)
        elif sSizeFormat.upper() == 'GB':
            return getBfromGB(fVal)
        elif sSizeFormat.upper() == 'TB':
            return getBfromTB(fVal)
        else:
            print('WTF!!!!!!!!')
    return None
    
def getBFromKB(fVal: float):
    return 1024*fVal

def getBfromMB(fVal: float):
    return 1024*getBFromKB(fVal)

def getBfromGB(fVal: float):
    return 1024*getBfromMB(fVal)

def getBfromTB(fVal: float):
    print(f'warning, TB!!!')
    return 1024*getBfromGB(fVal)

if __name__ == '__main__':
    wasdi.init("./config.json")
    run()