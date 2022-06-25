# %%# 

import os

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from selenium import webdriver
from selenium.webdriver.support.select import Select

# %#%#

url_page = "https://ifsc.results.info"

years = [str(year) for year in range(2022, 2024)] # 1990 2024

events = "Past events"
leagues = "World Cups and World Championships"
discipline = "Boulder"
cups = "All cups"

genders = ['M', 'W']

levels = ["Q", "S", "F"]

tabs = {"Q": ['Group A', 'Group B'],
        "S": ['Result'],
        "F": ['Result']}

base = ["Unique", "Year", "Discipline", "Competition", "Gender", "Level", "Group", "Name", "Number", "Country"]
scb = ["Top1", "Zone1", "Top2", "Zone2", "Top3", "Zone3", "Top4", "Zone4", "Top5", "Zone5"]
scl = ["Route1", "Route2"]
scs = ["Run1", "Run2", "Run3", "Run4", "Run5"]

columns = base + scb + scl + scs

back = "window.history.go(-1)"

wait = 2

file = "ifsc.xlsx"

def get_scores(strng):
    splt = strng.split("\n")
    lens = len(splt)
    score = [np.inf, np.inf]
    if lens == 3:
        score[0] = int(splt[0])
        score[1] = int(splt[1])
    if lens == 2:
        score[1] = int(splt[0])
    return score

def flatten_list(lst):
    new = []
    for lsi in lst:
        new += lsi
    return new

def go_back():
    # driver.execute_script(back)
    button = driver.find_elements_by_class_name('back-button')[0]
    button.click()
    return None

# %%#

try:
    driver
except Exception:
    driver = webdriver.Firefox()
driver.get(url_page)

# %#%#

if os.path.isfile(file):
    res = pd.read_excel(file)
else:
    print("Check directory, no ifsc.xlsx file found!")
    exit
    res = pd.DataFrame([], columns=columns)

# %#%#

for year in years:

    # year
    driver.implicitly_wait(wait)
    sels = driver.find_elements_by_class_name('custom-select')
    sels[0].click()
    select = Select(sels[0])
    select.select_by_visible_text(year)
    
    # event 
    driver.implicitly_wait(1)
    sels[1].click()
    select = Select(sels[1])
    select.select_by_visible_text(events)
    
    # league
    driver.implicitly_wait(1)
    sels[2].click()
    select = Select(sels[2])
    select.select_by_visible_text(leagues)
    
    # discipline
    driver.implicitly_wait(1)
    sels[3].click()
    select = Select(sels[3])
    select.select_by_visible_text(discipline)
    
    # cups
    driver.implicitly_wait(1)
    sels[4].click()
    select = Select(sels[4])
    select.select_by_visible_text(cups)
    
    driver.implicitly_wait(1)
    cards = driver.find_element_by_class_name('card-container').find_elements_by_tag_name("a")
    
    if not cards:
        print("nothing", year)
        continue
    
    for idk, card in enumerate(cards):
        cards = driver.find_element_by_class_name('card-container').find_elements_by_tag_name("a")
        card = cards[idk]
        comp = ' '.join(card.text.split('\n'))
        card.find_element_by_tag_name("div").click()
        
        if "CANCELLED" in comp:
            print("cancelled", comp)
            go_back()
            continue
        
        driver.implicitly_wait(1)
        disc = driver.find_element_by_xpath("//*[contains(text(), '%s')]" % discipline)
        disc.click()
        
        for idl, level in enumerate(levels):
            
            driver.implicitly_wait(1)
            elems = driver.find_elements_by_xpath("//*[contains(text(), '%s')]" % level)
            elems = [elem for elem in elems if elem.text == level]
            
            if not elems:
                print("nothing", year, comp, level)
                continue     
            
            for idg, gender in enumerate(genders):
            
                elems = driver.find_elements_by_xpath("//*[contains(text(), '%s')]" % level)
                elems = [elem for elem in elems if elem.text == level]
                
                try: # IFSC Climbing Worldcup (B) - Sheffield (GBR) 2010 no Women Semi                
                    elem = elems[idg] 
                except Exception:
                    print("missing", year, comp, level)
                    continue
                elem.click()
                tabz = tabs[level]
                
                for tab in tabz:
    
                    driver.implicitly_wait(1)
                    groups = driver.find_elements_by_xpath("//*[contains(text(), '%s')]" % tab)
                    groups = [group for group in groups if group.text == tab]
                    if not groups:
                        tab = "Result"
                        groups = driver.find_elements_by_xpath("//*[contains(text(), '%s')]" % tab)
                        groups = [group for group in groups if group.text == tab]
                    group = groups[0]
                    group.click()      
                    
                    unis = [year, discipline, comp, gender, level, tab]
                    uni = ';'.join(unis)   
                    uniz = [uni] + unis
                    
                    if uni in res['Unique'].unique():
                        print("skip", uni)
                        continue                           
                    
                    rei = pd.DataFrame([], columns=columns)
                
                    driver.implicitly_wait(1)
                    climbers = driver.find_elements_by_class_name('boulder-asc-detail')
                    climberz = driver.find_elements_by_class_name('r-name')
                    climberc = driver.find_elements_by_class_name('r-name-sub')
                    
                    for idc, climber in enumerate(climbers):                       
                    
                        name = climberz[idc].text
                        nuco = climberc[idc].text
                        try:
                            number, country = nuco.split(" • ")
                        except Exception:
                            number, country = "-", nuco
                        cli = [name, number, country]
                        print(*unis, *cli)    
                    
                        driver.implicitly_wait(1)
                        rnds = climber.find_elements_by_class_name('asc-cell-container')
        
                        scores = np.ravel(np.array([get_scores(rnd.text) for rnd in rnds]))
                        lens = len(scores)
                        print(scores)                        
                        
                        dct = dict()
                        for key, val in zip(base[:-3], uniz):
                            dct[key] = val
                        for key, val in zip(base[-3:], cli):
                            dct[key] = val
                        for key, val in zip(scb[:lens], scores):
                            dct[key] = val
                            
                        rei = rei.append(dct, ignore_index=True)
                                            
                    res = res.append(rei)
                    res.to_excel(file, index=False)


                # gender (after completing tabs/groups)
                go_back()

        # card (after completing card/comp)
        go_back()

# stop selenium
driver.quit()
 
# %%#
