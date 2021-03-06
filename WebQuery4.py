import sys
import time
import sqlite3
import datetime
import Database
import requests
from operator import itemgetter
import pandas as pd
from jinja2 import Environment, FileSystemLoader

pd.options.display.html.border = 0


class WebData:
    
    def __init__(self, year, series_id, race_id, feed_type):
        feeds = {
                0: 'live-feed',
                1: 'stage1-feed',
                2: 'stage2-feed',
                3: 'stage3-feed',
                10: 'live-qualifying-data',
                }
        self.feed = feeds[feed_type]
        self.url = f'https://www.nascar.com/live/feeds/series_{series_id}/{race_id}/{self.feed}.json'
        self.flag_dict = {
            1: 'Green',
            2: 'Yellow',
            3: 'Red',
            4: 'Checkered',
            8: 'Warm Up',
            9: 'Not Active',
			}

    def get_json(self):
        for i in range(5):
            try:
                page = requests.get(self.url)
                break
            except requests.exceptions.ConnectionError:
                print(f'request failed: retry {i}/5')
                time.sleep(5)
        status = page.status_code
        if status == 200:
            self.json = page.json()
        else:
            print('Page is not active')

    def get_driver_info(self):
        self.driver_list = []
        for i, car in enumerate(self.json['vehicles']):
            
            # Laps led
            laps_led = 0
            for led in car['laps_led']:                    
                if led['start_lap'] == 0:
                    if not led['end_lap'] == 0:
                        laps_led += led['end_lap'] - led['start_lap']
                else:
                    laps_led += led['end_lap'] - led['start_lap'] + 1                    
            if laps_led == 0:
                laps_led = None         
                
            # Pit Stops
            pit_stops = car['pit_stops']
            if pit_stops:
                last_stop = pit_stops[-1]['pit_in_lap_count']
                if last_stop == 0:
                    last_stop = ''
            else:
                last_stop = ''
            self.driver_list.append({
                'position'      :car['running_position'],
                'laps led'      :laps_led,
                'car number'    :car['vehicle_number'],
                'driver id'     :car['driver']['driver_id'],
                'driver name'   :car['driver']['full_name'],
                'delta'         :car['delta'],
                'lap time'      :car['last_lap_time'],
                'speed'         :car['last_lap_speed'],
                'last pit'      :last_stop,
                'sponsor'       :car['sponsor_name'],
                'qual'          :car['starting_position'],
                'manufacturer'  :car['vehicle_manufacturer']})
        for driver in self.driver_list:
            # Check eligibility
            if '(i)' in driver['driver name']:
                driver['ineligible'] = 1
            else:
                driver['ineligible'] = None #NULL
            # Check pole
            if driver['qual'] == 1:
                driver['pole'] = 1
            else:
                driver['pole'] = None
            # Format 'delta'
            if driver['delta'] < 0:
                driver['delta'] = int(driver['delta'])
            elif driver['position'] == 1:
                driver['delta'] = format(driver['lap time'], '.3f')
            else:
                driver['delta'] = format(driver['delta'], '.3f')
        self.driver_list.sort(key=itemgetter('position'))

    def get_race_info(self): 
        self.race_info = {
            'race id'      :self.json['race_id'],
            'series id'    :self.json['series_id'],
            'track id'     :self.json['track_id'],
            'race name'    :self.json['run_name'],
            'track name'   :self.json['track_name'],
            'track length' :self.json['track_length']  
            }

    def get_race_status(self):
        self.race_status = {
            'lap number'   :self.json['lap_number'],
            'total laps'   :self.json['laps_in_race'],
            'laps to go'   :self.json['laps_to_go'],
            'flag state'   :self.json['flag_state'],
            'elapsed time' :self.json['elapsed_time'],
            'time of day'  :self.json['time_of_day'],
            'cautions'     :self.json['number_of_caution_segments'],
            'caution laps' :self.json['number_of_caution_laps'],
            'lead changes' :self.json['number_of_lead_changes'],
            'leaders'      :self.json['number_of_leaders'],
#            'avg_diff_1to3':self.json['avg_diff_1to3']
            'stage_end'    :self.json['stage']['finish_at_lap']
            }
    
    def clean_driver_names(self):
        for driver in self.driver_list:
            driver['driver name'] = driver['driver name'].replace(' #', '')
            driver['driver name'] = driver['driver name'].replace('(i)', '')
            driver['driver name'] = driver['driver name'].replace('* ', '')
            driver['driver name'] = driver['driver name'].replace(' (P)', '')
        
    def fetch_names_from_DB(self):
        conn = sqlite3.connect('NASCAR.db')
        c = conn.cursor()
        self.name_list = []
        for driver in self.driver_list:
            c.execute('SELECT driver_name FROM Drivers WHERE driver_id=?',
                      (driver['driver id'],))
            name = c.fetchone()
            if name == None:
                self.name_list.append(f'ID {driver["driver id"]} not in database. Run "Database.update_drivers"')
            else:
                self.name_list.append(name[0]) 
        c.close()
        conn.close()


class Query:
    
    def __init__(self, WebData):
        self.qry = WebData

    def results(self, driver_only=False):
        self.qry.get_json()
        self.qry.get_driver_info()
        self.qry.get_race_info()
        self.qry.get_race_status()
        self.qry.fetch_names_from_DB()
        self._print_header()
        self._print_results(driver_only)
        
    def check_for_next_stage(self, prev_stage_lap):
        self.qry.get_json()
        self.qry.get_race_status()
        if self.qry.race_status['stage_end'] == prev_stage_lap:
            print('Pausing until next stage length is available')
            while self.qry.race_status['stage_end'] == prev_stage_lap:
                time.sleep(10)
                self.qry.get_json()
                self.qry.get_race_status()
            print('Stage length has been updated')
        
    def qual(self):
        self.qry.get_json()
        self.qry.driver_list = []
        for car in self.qry.json:
            self.qry.driver_list.append({
                'position':     car['position'],
                'driver id':    car['driver_id']})
        self.qry.fetch_names_from_DB()
        self.qry.driver_list.sort(key=itemgetter('position'))
        print(self.qry.name_list)
        print(self.qry.json[0]['qualifying_round'])
            
    def html_results(self, stage_lap=0):
        df = pd.DataFrame(self.qry.driver_list)
        df['driver name'] = self.qry.name_list
        cols = ['position', 'car number', 'driver name', 'delta', 'speed', 'last pit']
        new_cols = {'position': 'Pos', 
                    'car number': '#',
                    'driver name': 'Driver',
                    'delta': 'Delta',
                    'speed': 'Speed',
                    'last pit': 'Last Pitted',
                    }
        df = df[cols]
        df = df.rename(columns=new_cols)
        header = f"""{self.qry.race_info['race name']}<br/>
                     {self.qry.race_info['track name']}"""
        flag_state = self.qry.race_status['flag state']
        if flag_state in self.qry.flag_dict:
            status = f"{self.qry.flag_dict[flag_state]}<br/>"
        else:
            status = f"Flag {flag_state} not defined<br/>"
        current_lap = self.qry.race_status['lap number']
        if not stage_lap == 0:
            total_laps = stage_lap
            to_go = total_laps - current_lap
        else:
            total_laps = self.qry.race_status['total laps']
            to_go = self.qry.race_status['laps to go']
        status = f"""{status}
                     Lap: {current_lap}/{total_laps}<br/>
                     {to_go} laps to go<br/>
                     Elapsed: {datetime.timedelta(seconds=self.qry.race_status['elapsed time'])}"""
        env = Environment(loader=FileSystemLoader('templates'))
        template = env.get_template('template.html')
        f = open("templates/table.html",'w')
        f.write(template.render(header=header, status=status, table=df.to_html(index=False),))
        f.close()
        
    def _print_header(self, stage_lap=0):
        print('')
        print(f"\n{self.qry.race_info['race name']}")
        print(f"{self.qry.race_info['track name']}\n")
        flag_state = self.qry.race_status['flag state']
        if flag_state in self.qry.flag_dict:
            print(f'Flag: {self.qry.flag_dict[flag_state]}')
        else:
            print(f'Flag {flag_state} not defined')
        current_lap = self.qry.race_status['lap number']
        if not stage_lap == 0:
            total_laps = stage_lap
            to_go = total_laps - current_lap
        else:
            total_laps = self.qry.race_status['total laps']
            to_go = self.qry.race_status['laps to go']
        print(f'Lap: {current_lap}/{total_laps}')
        print(f'{to_go} laps to go')
        print(f"Elapsed: {datetime.timedelta(seconds=self.qry.race_status['elapsed time'])}\n")
    
    def _print_results(self, driver_only=False):
        if driver_only == False:
            print('{:^4}{:^8}{:22}{:^7}{:^15}'.format('Pos', '#', 'Driver', 'Delta', 'Speed'))
            print('-----------------------------------------------------')
            for driver, name in zip(self.qry.driver_list, self.qry.name_list):
                print(f"""{driver['position']:^4}{driver['car number']:^8}{name:22}{driver['delta']:^7}{driver['speed']:^15}""")
        else:
            for name in self.qry.name_list:
                print (name)

    def live_race(self, stage_lap=0, refresh=3, results_pause=10):
        live = Database.LiveRace()
        prev_lap = -1
        prev_flag = -1
        print('\nRace monitoring has started\n')
        while True:
            self.qry.get_json()
            self.qry.get_race_status()
            
            flag_state = self.qry.race_status['flag state']
            lap = self.qry.race_status['lap number']
            total_laps = self.qry.race_status['total laps']
            if stage_lap == 0:
                crit_lap = total_laps
            else:
                crit_lap = stage_lap
            # Yellow flag and stage end
            if flag_state != 1 and lap >= crit_lap: 
                print('\nGetting Running Order...')
                print(f'Pausing {results_pause} seconds...')
                time.sleep(results_pause)
                self.qry.get_json()
                self.qry.get_driver_info()
                self.qry.get_race_info()
                self.qry.get_race_status()
                self.qry.fetch_names_from_DB()
                self.html_results(stage_lap=stage_lap)
                live.add_lap(self.qry.driver_list, self.qry.race_status)
                break
            else:
                # new lap or new flag
                if lap != prev_lap or flag_state != prev_flag: 
                    self.qry.get_driver_info()
                    self.qry.fetch_names_from_DB()
                    self.html_results(stage_lap=stage_lap)
                    live.add_lap(self.qry.driver_list, self.qry.race_status)
                prev_lap = lap
                prev_flag = flag_state
                time.sleep(refresh)