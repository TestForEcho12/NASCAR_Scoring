import WebQuery3
import Database
import excel
import social

year = 2018
series_id = 1
race_id = 4676
track = '@DISupdates'
hashtag = '#DAYTONA500'


# set up live feed web object
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=0)

# query object and return inital results
qry = WebQuery3.Query(web)
qry.results()

# Database object, load web object, add race and results to DB
db = Database.Database()
fetch = Database.Fetch()
db.web_query(web)
db.update_drivers()
db.add_race(year=year)
db.add_results()

# Qual results to Excel
csv_col = 'xxxx'
fetch.results_to_csv(race_id=race_id, stage_id=0, col=csv_col)
excel.full_run(series=series_id)

# Set up live race position tracking
live = Database.LiveRace()
live.add_table(qry.qry.driver_list)

# initalize social accounts
reddit = social.reddit()
reddit_id = reddit_id = reddit.get_id('Race Thread')
twitter = social.twitter()


# Stage 1
stage = 1
stage_lap = 60
csv_col = '5'

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=10)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
excel.calculate_points(series=series_id)
excel.export_pictures(series=series_id)

reddit = social.reddit()
twitter = social.twitter()
comment = social.imgur_upload(stage=stage)
twitter.top_10(qry.qry.name_list)
reddit.comment(url_id=reddit_id, comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track, hashtag=hashtag)

# TEST: Check for Stage 1 JSON
web = WebQuery3.WebData(year=year, series_id=series_id, race_id=race_id, feed_type=1)
qry = WebQuery3.Query(web)
qry.results()


# Stage 2
stage = 2
stage_lap = 120
csv_col = '6'

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=10)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
excel.calculate_points(series=series_id)
excel.export_pictures(series=series_id)

reddit = social.reddit()
twitter = social.twitter()
comment = social.imgur_upload(stage=stage)
twitter.top_10(qry.qry.name_list)
reddit.comment(url_id=reddit_id, comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track, hashtag=hashtag)



# Finish
stage = 9
stage_lap = 0
csv_col = '7'

qry.live_race(stage_lap=stage_lap, refresh=3, results_pause=30)
db.web_query(web)
db.update_results(stage=stage)
fetch.results_to_csv(race_id=race_id, stage_id=stage, col=csv_col)
fetch.laps_to_csv(series=series_id, year=year)
excel.calculate_points(series=series_id)
excel.export_pictures(series=series_id)

reddit = social.reddit()
twitter = social.twitter()
comment = social.imgur_upload(stage=stage)
twitter.top_10(qry.qry.name_list)
reddit.comment(url_id=reddit_id, comment=comment)
twitter.standings(srs=series_id, stg=stage, track=track, hashtag=hashtag)


# Post Race
reddit_id = reddit.get_id('Post-Race')
reddit.comment(url_id=reddit_id, comment=comment)
#reddit_id = reddit.get_id('Scorecard')
#reddit.comment(url_id=reddit_id, comment=comment)
