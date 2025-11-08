import pandas as pd

df = pd.read_csv("matches.csv")

print("Q1")
print(f"Total number of matches: {len(df)}\n")
print("Column names:")
print(list(df.columns))
print("\nFirst 5 rows:")
print(df.head(5))
print("\nDescribe:")
print(df.describe(include='all').transpose())

print("\nQ2")
final_ball = df[(df['win_by_runs'] == 1) | (df['win_by_wickets'] == 1)]
pom_cnt = final_ball['player_of_match'].value_counts()
top_player = pom_cnt.idxmax()
top_count = pom_cnt.max()
print(f"\nPlayer with most Player of the Match awards in final-ball games: {top_player} ({top_count} awards)")

print("\nQ3")
wankhede = df[df['venue'].str.contains('Wankhede')]
runs = (wankhede['win_by_runs'] > 0).sum()
wickets = (wankhede['win_by_wickets'] > 0).sum()
if runs > wickets:
        print("At Wankhede Stadium it's more common to win by batting first (runs).")
elif wickets > runs:
    print("At Wankhede Stadium it's more common to win by batting second (wickets).")
else:
    print("At Wankhede Stadium wins by runs and by wickets are equally common (tie).")

print("\nQ4")
wins = df[df['win_by_runs'] > 50]
team_counts = wins['winner'].value_counts()
print(team_counts)
top_team = team_counts.idxmax()
print(f"\nTeam with  the highest number of wins: {top_team}")

print("\nQ5")
cond = (df['toss_winner'] == df['winner']) & (df['toss_decision'].fillna('').str.lower() == 'bat')
count_req= cond.sum()
print(f"Number of matches : {int(count_req)}")

print("\nQ6")
kkr = df[(df['team1'] == 'Kolkata Knight Riders') | (df['team2'] == 'Kolkata Knight Riders')]
ump1_val = kkr['umpire1'].sum()
ump2_val = kkr['umpire2'].sum()
if ump1_val > ump2_val:
    win = 'umpire1'
elif ump2_val > ump1_val:
    win = 'umpire2'
else:
    win = 'tie'
print(f"Umpires who has officiated more matches involving the  Kolkata Knight Riders: {win}")