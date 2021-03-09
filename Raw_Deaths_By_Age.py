import plotly.express as px
import pandas as pd
from datetime import date

# Tells Pandas to display everything when printing Dataframes. Used for debugging
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


# deaths = pd.read_csv('Data/Deaths/Deaths_Divergence_2021-03-02.csv')
deaths = pd.read_csv('https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&metric=newDeaths28DaysByDeathDateAgeDemographics&format=csv')


# Remove extraneous data
deaths = deaths[['date', 'age', 'deaths']]
deaths = deaths.loc[(deaths['age'] != '60+') & (deaths['age'] != '00_59')]


# Convert date string to datetime format for aligning peaks
deaths['date'] = pd.to_datetime(deaths['date'])
deaths['date'] = deaths['date'].dt.date


# Create buckets to group API data for Under/Over 80s
under60s = ['00_04', '10_14', '15_19', '20_24', '25_29',
            '30_34', '35_39', '40_44', '45_49', '50_54',
            '55_59']

sixties = ['60_64', '65_69']

seventies = ['70_74', '75_79']

over80s = ['80_85', '85_89', '90+']


# Create two new Dataframes from bucketed API data for Under/Over 80s
under60 = deaths.loc[deaths['age'].isin(under60s)].copy()
over80 = deaths.loc[deaths['age'].isin(over80s)].copy()
seventy = deaths.loc[deaths['age'].isin(seventies)].copy()
sixty = deaths.loc[deaths['age'].isin(sixties)].copy()

# Group and sum daily deaths for Under 80s and rename column for housekeeping
under60 = under60[['date', 'deaths']]
under60 = under60.groupby(['date'], as_index=False).sum()
under60['age'] = "Under60"

# Group and sum daily deaths for Under 80s and rename column for housekeeping
over80 = over80[['date', 'deaths']]
over80 = over80.groupby(['date'], as_index=False).sum()
over80['age'] = "Over80"

# Group and sum daily deaths for Under 80s and rename column for housekeeping
seventy = seventy[['date', 'deaths']]
seventy = seventy.groupby(['date'], as_index=False).sum()
seventy['age'] = "Seventies"

# Group and sum daily deaths for Under 80s and rename column for housekeeping
sixty = sixty[['date', 'deaths']]
sixty = sixty.groupby(['date'], as_index=False).sum()
sixty['age'] = "Sixties"

divergence = pd.concat([under60, sixty, seventy, over80])
divergence.sort_values(['date', 'age'], inplace=True)

# divergence = divergence.loc[divergence['date'] >= '2020-09-01']
divergence.reset_index(inplace=True)

# divergence.sort_values(['date', 'age'], inplace=True)
print(divergence)
last_date = divergence['date'].iloc[-1]

# Prepare chart to show daily divergence
divergence_plot = px.line(divergence, x='date', y='deaths', title='England: COVID Deaths',
                          color='age', template='seaborn', labels={'date': '', 'deaths': 'Deaths'})

divergence_plot.add_vrect(x0="2020-03-23", x1="2020-05-18",
                          fillcolor="green", opacity=0.2, line_width=0)
divergence_plot.add_annotation(x='2020-04-28', y=510,
                               text="Lockdown<br>1.0",
                               showarrow=False, xshift=5)

divergence_plot.add_vrect(x0="2020-11-05", x1="2020-12-02",
                          fillcolor="green", opacity=0.2, line_width=0)
divergence_plot.add_annotation(x='2020-11-17', y=510,
                               text="Lockdown<br>2.0",
                               showarrow=False, xshift=5)

divergence_plot.add_vrect(x0="2021-01-06", x1=last_date,
                          fillcolor="green", opacity=0.2, line_width=0)
divergence_plot.add_annotation(x='2021-02-10', y=510,
                               text="Lockdown<br>3.0",
                               showarrow=False, xshift=5)

# Housekeeping for chart, setting fonts etc
divergence_plot.update_xaxes(nticks=20)
divergence_plot.update_annotations(align='center')
divergence_plot.update_layout(
    font_family="Helvetica",
    font_color="black",
    font_size=16,
    title_font_family="Helvetica",
    title_font_color="black",
    title_font_size=22,
    title_x=0.5
)

# Create a daily timestamp for filenames to prevent overwriting
timestamp = str(date.today())

# Saves chart as interactive HTML, with hover/rollover functions
divergence_plot.write_html('Charts/Raw Data/Deaths_Raw_' + timestamp + '_interactive.html')


# Saves chart as static PNG file
divergence_plot.write_image('Charts/Raw Data/Deaths_Raw_' + timestamp + '_static.png')

# Save raw data as CSV
divergence.to_csv('Data/Raw Data/Deaths_Raw_' + timestamp + '.csv', index=False)

# Show chart in browser
divergence_plot.show()