import altair as alt
import pandas as pd
import streamlit as st
import seaborn as sns
from espn_api.football import League
import matplotlib.pyplot as plt

# Initialize the ESPN Fantasy Football League object using the provided credentials
espn2 = 'AECl%2FJRiKzdXd%2BjpBaTBHeFcf4WliuEfvXxjLuEpauhEO%2Bh5aXeGgCxErZD%2BoWGmt9vBEQ%2FR1HDLmW4InCF4%2FSB9OVe9IGV4YNFD%2FxGfNNeIIryLUjJr%2FseSXSpjhl%2B0%2B8qJ86oI2dFDOtORSZsLpz4exqV2oO6wQXGeqsGEvzU2DcPrfr%2FiD%2FrosV1oawvNS0fNBG0IZ8L1Aa9E0PxYksm%2BXV5rrjP7wGUoihgCppcDrx6A5amW3%2BCDSJOlsRezH18qo4xM5eyKNilLtzbH%2Bjom4RA%2Frg9nbEQw2OuoOq%2F2McxnegmbY7fBqdHtLRtoFpc%3D'
swid = '{131F0BE6-6541-4014-9F0B-E66541B01431}'
league = League(league_id=1254749, year=2024, espn_s2=espn2, swid=swid)

# Page Configuration and Title
st.set_page_config(page_title="Fantasy Football Performance Tracker")
st.title("Fantasy Football Team Performance: Projected vs Actual Points")

st.write("""
This app visualizes both team and player performances in our fantasy football league.
Explore:
- A **heatmap** of teams' weekly performance differences (actual vs projected points).
- **Bar charts** for total team points in selected weeks.
- **Top Player Rankings** for each position (ranked by total points scored).
""")

### SECTION: REFRESH BUTTON ###
# Initialize the session state for tracking refresh
if "refresh_count" not in st.session_state:
    st.session_state["refresh_count"] = 0  # Track how many times refresh happens

# Create a refresh button
if st.button('🔄 Refresh Data'):
    st.session_state["refresh_count"] += 1  # Increment the refresh count
    
    # Clear the cache by resetting the cached data
    st.cache_data.clear()  # Clear cached data for team and player loading functions

    st.success("Data refreshed successfully! 🎉")

# Show the current refresh count in the UI (for reference)
st.write(f"Data refreshed {st.session_state['refresh_count']} time(s).")

### TEAM-LEVEL DATA LOADING ###
# Function to load data at the team level (using caching)
@st.cache_data
def load_team_data():
    all_data = []
    
    total_weeks = 12  # Adjust for appropriate number of weeks in the season
    for week in range(1, total_weeks + 1):
        box_scores = league.box_scores(week)
        for box_score in box_scores:
            # Home and Away teams' actual vs projected
            home_team_data = {
                'Team': box_score.home_team.team_name,
                'Week': week,
                'Actual Points': box_score.home_score,
                'Projected Points': sum(player.projected_points for player in box_score.home_lineup)
            }
            away_team_data = {
                'Team': box_score.away_team.team_name,
                'Week': week,
                'Actual Points': box_score.away_score,
                'Projected Points': sum(player.projected_points for player in box_score.away_lineup)
            }
            all_data.extend([home_team_data, away_team_data])
    
    # Create DataFrame and add Difference column
    df = pd.DataFrame(all_data)
    df['Difference'] = df['Actual Points'] - df['Projected Points']
    
    return df

# Function to load player data (using caching)
@st.cache_data
def load_player_data():
    all_player_data = []

    total_weeks = 12  # Adjust for appropriate number of weeks in the season

    # Loop through each week and fetch player-related data
    for week in range(1, total_weeks + 1):
        box_scores = league.box_scores(week)
        for box_score in box_scores:
            # Process home team players
            for player in box_score.home_lineup:
                player_data = {
                    'Team': box_score.home_team.team_name,  # Use team name from box score
                    'Player Name': player.name,
                    'Position': getattr(player, 'position', 'Unknown'),  # Defensive programming
                    'Week': week,
                    'Points Scored': getattr(player, 'points', 0),
                    'Projected Points': getattr(player, 'projected_points', 0),
                    'Position Rank': getattr(player, 'posRank', 'N/A')  # Assume position rank might be undefined
                }
                all_player_data.append(player_data)
            
            # Process away team players
            for player in box_score.away_lineup:
                player_data = {
                    'Team': box_score.away_team.team_name,  # Use team name from box score
                    'Player Name': player.name,
                    'Position': getattr(player, 'position', 'Unknown'),
                    'Week': week,
                    'Points Scored': getattr(player, 'points', 0),
                    'Projected Points': getattr(player, 'projected_points', 0),
                    'Position Rank': getattr(player, 'posRank', 'N/A')
                }
                all_player_data.append(player_data)
    
    # Create a DataFrame from collected player data
    player_df = pd.DataFrame(all_player_data)
    return player_df

# Load the team and player data with caching and refresh capability
team_df = load_team_data()
player_df = load_player_data()

### DISPLAYING TEAM-LEVEL DATA (Like before) ###
# User Input: Select specific teams to visualize
teams = st.multiselect(
    "Select teams to visualize:",
    team_df.Team.unique(),
    default=team_df.Team.unique()  # Default to all teams selected
)

# User Input: Range of weeks
weeks = st.slider("Select the week range:", 1, 12, (1, 2))

# Filter Data Based on Team Selection and Selected Weeks
df_filtered = team_df[
    (team_df["Team"].isin(teams)) & (team_df["Week"].between(weeks[0], weeks[1]))
]

# HEATMAP SECTION
st.subheader("Heatmap: Team Performance (Difference Between Actual vs Projected Points)")
if not df_filtered.empty:
    heatmap_data = df_filtered.pivot(index='Team', columns='Week', values='Difference')

    plt.figure(figsize=(12, 8))
    sns.heatmap(heatmap_data, cmap='RdYlGn', center=0, annot=True, fmt='.1f')
    plt.title('Weekly Performance Difference: Actual vs Projected', fontsize=16)
    plt.xlabel('Week', fontsize=12)
    plt.ylabel('Team', fontsize=12)
    st.pyplot(plt)
else:
    st.write("No data available for the selected teams and weeks.")

# BAR CHART SECTION (Total Points for Week)
st.subheader(f"Bar Chart: Points for the Selected Week")
current_week_df = df_filtered[df_filtered["Week"] == weeks[1]]

if not current_week_df.empty:
    bar_chart = alt.Chart(current_week_df).mark_bar().encode(
        x=alt.X('Team:N', title='Team'),
        y=alt.Y('Actual Points:Q', title='Points Scored'),
        color=alt.condition(
            alt.datum['Actual Points'] > alt.datum['Projected Points'],
            alt.value("green"),
            alt.value("red")
        )
    ).properties(
        title=f'Total Actual Points in Week {weeks[1]}',
        width=600,
        height=400
    )
    st.altair_chart(bar_chart, use_container_width=True)
else:
    st.write(f"No data available for Week {weeks[1]} with the current team selection.")
