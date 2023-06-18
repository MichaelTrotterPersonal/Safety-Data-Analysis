# Python standard library
import os
import pickle

# Additional dependencies 
import pandas as pd

# Data paths
DATA_DIR = r"data"
EVENTS_PATH = os.path.join(DATA_DIR,r"Reported_Events.csv")
BLUE_PATH = os.path.join(DATA_DIR,r"Monthly_Aircraft_Movements_Blue_City.csv")
GREEN_PATH = os.path.join(DATA_DIR,r"Monthly_Aircraft_Movements_Green_City.csv")
RED_PATH = os.path.join(DATA_DIR,r"Monthly_Aircraft_Movements_Red_City.csv")
YELLOW_PATH = os.path.join(DATA_DIR,r"Monthly_Aircraft_Movements_Yellow_City.csv")
PROCESSED_OUT_PATH = os.path.join(DATA_DIR,r"processed_data.pkl")
SELECTED_OUT_PATH = os.path.join(DATA_DIR,r"selected_data.pkl")

def get_movements_data(year: int=2022) -> pd.DataFrame:
    """Returns the movements data filtered to a specific year as a pd.DataFrame.

    Args:
        year (int, optional): The year to filter the data on. Defaults to 2022.

    Returns:
        pd.DataFrame: the events data for the year requested.
    """
        
    # Read in the city movement data, filter to 2022 only, store as one merged DF
    blue_df = pd.read_csv(BLUE_PATH,names=['datetime','n_movements'],header=0)
    blue_df['Location'] = 'Blue City'
    green_df = pd.read_csv(GREEN_PATH,names=['datetime','n_movements'],header=0)
    green_df['Location'] = 'Green City'
    red_df = pd.read_csv(RED_PATH,names=['datetime','n_movements'],header=0)
    red_df['Location'] = 'Red City'
    yellow_df = pd.read_csv(YELLOW_PATH,names=['datetime','n_movements'],header=0)
    yellow_df['Location'] = 'Yellow City'

    movements_df = pd.concat([blue_df, green_df, red_df, yellow_df])
    movements_df.datetime = pd.to_datetime(movements_df.datetime,format="%d/%m/%Y %H:%M:%S")
    movements_df = movements_df[movements_df.datetime.dt.year==year].copy().reset_index(drop=True) 
    movements_df['month'] = movements_df.datetime.dt.to_period('M')

    return movements_df

def get_events_data(year: int=2022) -> pd.DataFrame:
    """Returns the events data filtered to a specific year as a pd.DataFrame.

    Args:
        year (int, optional): The year to filter the data on. Defaults to 2022.

    Returns:
        pd.DataFrame: the events data for the year requested.
    """
    
    # Read in the events data, filter to 2022 only
    events_df = pd.read_csv(EVENTS_PATH)
    events_df.Event_Date = pd.to_datetime(events_df.Event_Date,format="%d-%m-%y")
    events_df = events_df[events_df.Event_Date.dt.year==year].copy().reset_index(drop=True)
    events_df['month'] = events_df.Event_Date.dt.to_period('M')

    return events_df

def get_blank_df(event_types: list, locations: list, year: int=2022) -> pd.DataFrame:
    """Create a DataFrame with one row for each event type/location/month combination.
    This will be merged with the event data and non-matching rows filled with 0 counts for events.

    Args:
        event_types (list): A list of event type strings
        locations (list): A list of location strings
        year (int): An integer year 

    Returns:
        pd.DataFrame: a DataFrame with one row for each event type/location/month combination
    """
 
    start, end = f"{year}-01", f"{year}-12"

    months = pd.Series(pd.period_range(start=start, end=end, freq='M'))
    months = pd.concat([months] * len(event_types)).reset_index(drop=True)
    
    events = pd.Series(event_types)
    events = events.repeat(len(months)/len(event_types)).reset_index(drop=True)
    
    df = pd.DataFrame({'month':months,'Event_Type':events})
    res_df = pd.concat([df]*len(locations)).reset_index(drop=True)
    res_df['Location'] = pd.Series([loc for loc in locations for _ in range(len(df))])

    return res_df

def get_combined_df(movements_df: pd.DataFrame, events_df: pd.DataFrame, blank_df: pd.DataFrame) -> pd.DataFrame:
    
    # Get the events for this city
    events_df = events_df.groupby(['Event_Type','month','Location']).count().iloc[:,[0]].rename(columns={'Event_ID':'n_events'}).reset_index()

    # Join the city_events_df to blank df - this adds the 0 event types in a month to the data
    res_df = pd.merge(blank_df,events_df,on=['month','Event_Type','Location'],how='left')
    res_df = res_df.fillna(0)
    
    # Add the movements values, calculate the event rates, sort by month and add the text month name
    res_df = pd.merge(res_df,movements_df,on=["month","Location"])
    res_df['event_rate'] = res_df.n_events/(res_df.n_movements/1000)
    
    # Add rows that correspond to the values for all cities combined
    all_df = res_df.groupby(['month','Event_Type']).sum().reset_index()
    all_df.event_rate = all_df.n_events/(all_df.n_movements/1000)
    all_df['Location'] = 'All Cities'
    
    # Merge the city-specific with the 'All Cities' df 
    res_df = pd.concat([res_df,all_df])
    
    # Add an 'All Types' category of event type
    all_types = res_df.groupby(['month','Location']).sum().reset_index()
    all_types = all_types.drop('n_movements',axis=1)
    all_types['Event_Type'] = "All Types"

    # Reset the movement numbers for the All Types category as these are changed by the groupby above
    n_movements = res_df.groupby(['Location','month']).max().n_movements.reset_index()
    all_types = pd.merge(all_types,n_movements,on=['Location','month'])

    res_df = pd.concat([all_types,res_df])
    
    # Sort by month
    res_df = res_df.sort_values('month').reset_index(drop=True)
    res_df.month = res_df.month.dt.strftime('%B')
    res_df = res_df.drop('datetime',axis=1)
    
    return res_df

if __name__ == "__main__":
    
    events_df = get_events_data()
    movements_df = get_movements_data()
    
    event_types = list(events_df.Event_Type.unique())
    locations = list(movements_df.Location.unique())
    processed_df = get_combined_df(movements_df,events_df,get_blank_df(event_types,locations))

    selected_los = events_df[events_df.Event_Type=='Loss of Separation']
    selected_fac = events_df[(events_df.Location=='Red City')&(events_df.month=='2022-05')&(events_df.Event_Type=='Facility Issue')]
    selected_df = pd.concat([selected_los,selected_fac])

    with open(PROCESSED_OUT_PATH, "wb") as file:
        pickle.dump(processed_df, file)

    with open(SELECTED_OUT_PATH, "wb") as file:
        pickle.dump(selected_df, file)