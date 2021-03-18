import plotly.express as px
import pandas as pd
from datetime import date

# Tells Pandas to display everything when printing Dataframes. Used for debugging
pd.set_option('display.max_rows', None)
pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)
pd.set_option('display.max_colwidth', None)


# Download data from API and load into Dataframe
deaths_data = pd.read_csv('https://api.coronavirus.data.gov.uk/v2/data?areaType=nation&metric=newDeaths28DaysByDeathDateAgeDemographics&format=csv')


# Remove extraneous data
deaths_data = deaths_data[['date', 'age', 'deaths']]
deaths_data = deaths_data.loc[(deaths_data['age'] != '60+') & (deaths_data['age'] != '00_59')]


# Convert date string to datetime format for aligning peaks
deaths_data['date'] = pd.to_datetime(deaths_data['date'])


# Create buckets to group API data for Under/Over 80s
under80s = ['00_04', '10_14', '15_19', '20_24', '25_29',
            '30_34', '35_39', '40_44', '45_49', '50_54',
            '55_59', '60_64', '65_69', '70_74', '75_79']

over80s = ['80_84', '85_89', '90+']


# Create two new Dataframes from bucketed API data for Under/Over 80s
under80 = deaths_data.loc[deaths_data['age'].isin(under80s)].copy()
over80 = deaths_data.loc[deaths_data['age'].isin(over80s)].copy()


# Group and sum daily deaths for Under 80s and rename column for housekeeping
under80 = under80.groupby(['date'], as_index=False).sum()
under80.rename(columns={'deaths': 'deaths_under80'}, inplace=True)


# Identify peak deaths and calculate daily percentage below peak for Under 80s
under80peak = under80['deaths_under80'].max()
under80['percent_peak_under80'] = round((100 / under80peak) * under80['deaths_under80'], 2)


# Group and sum daily deaths for Over 80s and rename column for housekeeping
over80 = over80.groupby(['date'], as_index=False).sum()
over80.rename(columns={'deaths': 'deaths_over80'}, inplace=True)


# Identify peak deaths and calculate daily percentage below peak for Over 80s
over80peak = over80['deaths_over80'].max()
over80['percent_peak_over80'] = round((100 / over80peak) * over80['deaths_over80'], 2)


# Identify date of peak deaths for Under/Over 80s
over80days = over80.query('deaths_over80 == deaths_over80.max()')['date'].values[0]
under80days = under80.query('deaths_under80 == deaths_under80.max()')['date'].values[0]


# Calculate difference in date of peaks and time-shift them into alignment
align_peaks = over80days - under80days
under80['date'] = under80['date'] + pd.Timedelta(align_peaks)


# Merge Under/Over80s Dataframes by date to create a new Dataframe.
# Uses Inner Join to drop extraneous data after time-shifting
divergence = pd.merge(over80, under80, how='inner', left_on='date', right_on='date')
divergence.reset_index(inplace=True)


# Calculate "divergence" as difference between percentage below peaks for Under/Over 80s
divergence['divergence'] = round(divergence['percent_peak_over80'] - divergence['percent_peak_under80'], 2)


# Calculate "daily change" in divergence and reset first value to zero
divergence['daily_change'] = round(divergence['divergence'].diff(1), 2)
divergence['daily_change'].fillna(0, inplace=True)


# Tidy up Dataframe and reorganise columns for readability
divergence = divergence[['date', 'deaths_over80', 'deaths_under80',
                         'percent_peak_over80', 'percent_peak_under80',
                         'divergence', 'daily_change']]
divergence.sort_values('date', ascending=False, inplace=True)
divergence.reset_index(inplace=True, drop=True)


# Create a daily timestamp for filenames to prevent overwriting
timestamp = str(date.today())


# Dump Divergence Dataframe to CSV file, with timestamp for a daily record
divergence.to_csv('Data/Deaths/Deaths_Divergence_' + timestamp + '.csv', index=False)



# Prepare chart to show daily divergence
divergence_plot = px.line(divergence, x='date', y='divergence', title='England: Proportion of COVID Deaths in Under/Over 80s<br>Comparative Divergence From Temporally Aligned Peaks',
                          template='seaborn', labels={'date': '', 'divergence': 'Comparative Divergence'})


# Get first and last date of Dataframe. Used for positioning annotations
first_date = divergence['date'].iloc[-1]
last_date = divergence['date'].iloc[0]


# Set markers for boundline annotations. Hard coded due to laziness and to change inputs
top_boundline = 10
bottom_boundline = -13


# Add boundline annotations to chart
divergence_plot.add_hline(y=bottom_boundline, line_width=2, line_dash="dot", line_color="blue", opacity=0.7)
divergence_plot.add_hline(y=top_boundline, line_width=2, line_dash="dot", line_color="blue", opacity=0.7)
divergence_plot.add_hline(y=0, line_width=2, line_dash="dash", line_color="blue", opacity=0.7)


# Adds shaded green box and text annotations for 1st Wave
divergence_plot.add_vrect(x0="2020-03-27", x1="2020-05-02",
                          fillcolor="green", opacity=0.3, line_width=0)
divergence_plot.add_annotation(x='2020-04-12', y=25,
                               text="First<br>Wave",
                               showarrow=False, xshift=5)
divergence_plot.add_annotation(x='2020-05-02', y=-25,
                               text="Unrecorded<br>Deaths",
                               showarrow=False)


# Adds shaded green box and text annotations for vaccination period
divergence_plot.add_vrect(x0="2021-01-24", x1=last_date,
                          fillcolor="green", opacity=0.3, line_width=0)
divergence_plot.add_annotation(x='2021-01-21', y=-25,
                               text="Vaccine<br>Divergence",
                               showarrow=False)
divergence_plot.add_annotation(x='2021-02-05', y=23,
                               text="79.71%<br>Over80s<br>(1 dose)",
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


# Saves chart as interactive HTML, with hover/rollover functions
divergence_plot.write_html('Charts/Deaths/Deaths_Divergence_' + timestamp + '_interactive.html')


# Saves chart as static PNG file
divergence_plot.write_image('Charts/Deaths/Deaths_Divergence_' + timestamp + '_static.png')


# Displays chart in browser
divergence_plot.show()