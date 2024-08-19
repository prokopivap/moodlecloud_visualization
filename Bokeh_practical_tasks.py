# bokeh serve --show Bokeh_practical_tasks.py
# kill -9 <pid>


import pandas as pd
import numpy as np
import os
from bokeh.io import show, curdoc
from bokeh.models import ColumnDataSource, HoverTool, Select, FactorRange
from bokeh.layouts import column, row
from bokeh.plotting import figure, output_file, save
from bokeh.transform import factor_cmap

script_dir = os.path.dirname(os.path.abspath(__file__))
source_path = script_dir

def prepare_data_for_processing():

    #script_dir = os.path.dirname(os.path.abspath(__file__))
    #source_path = script_dir + '/Titanic/'

    df = pd.read_csv(source_path + '/Titanic/Titanic-Dataset.csv')

    # Handle missing values
    df['Age'].fillna(df['Age'].median(), inplace=True)
    df['Cabin'].fillna('Unknown', inplace=True)
    df['Embarked'].fillna('N/A', inplace=True)
    #df.isna().sum()

    df['AgeGroup'] = np.where(df['Age'] < 11, 'Child',
                        np.where(df['Age'] < 20, 'Young Adult',
                                np.where(df['Age'] < 60, 'Adult', 'Senior')
                                )
                            )

    grouped_df = df.groupby(['Pclass', 'Sex', 'AgeGroup'])['Survived'].mean().reset_index()
    #display(grouped_df)

    grouped_df['SurvivalRate'] = (grouped_df['Survived'] * 100).round(2)

    # Merge (grouped_df) with (df)
    df_survived = pd.merge(df, grouped_df[['Pclass', 'Sex', 'AgeGroup', 'SurvivalRate']],
                on=['Pclass', 'Sex', 'AgeGroup'], how='left')

    return df_survived



# Age Group Survival: Create a bar chart showing survival rates across different age groups.
# Calculate survival rates for each AgeGroup
def age_group_survival(df_survived):
    age_group_survival = df_survived.groupby('AgeGroup')['Survived'].mean() * 100
    age_group_survival = age_group_survival.reset_index()
    age_group_survival['AgeGroup'] = age_group_survival['AgeGroup'].astype(str)

    # Convert to ColumnDataSource for Bokeh
    source = ColumnDataSource(age_group_survival)

    # Figure craete
    p = figure(x_range=age_group_survival['AgeGroup'].unique().tolist(), height=500, width=700,
            title="Survival Rates by Age Group", toolbar_location=None, tools="")

    # Add bars
    p.vbar(x='AgeGroup', top='Survived', width=0.9, source=source, color='skyblue')

    # Add hover tool
    hover = HoverTool()
    hover.tooltips = [
        ("Age Group", "@AgeGroup"),
        ("Survival Rate", "@Survived{0.2f}%")
    ]
    p.add_tools(hover)

    p.y_range.start = 0
    p.yaxis.axis_label = "Survival Rate (%)"
    p.xaxis.axis_label = "Age Group"

    # Create filtering widgets
    class_select = Select(title="Passenger Class", value="All", options=["All", "1", "2", "3"])
    gender_select = Select(title="Gender", value="All", options=["All", "male", "female"])

    # Update function to filter data based on selection
    def update():
        selected_class = class_select.value
        selected_gender = gender_select.value

        # Filter df_survived based on the selected class and gender
        filtered_df = df_survived.copy()

        if selected_class != "All":
            filtered_df = filtered_df[filtered_df['Pclass'] == int(selected_class)]
        if selected_gender != "All":
            filtered_df = filtered_df[filtered_df['Sex'] == selected_gender]

        # Recalculate the survival rates by AgeGroup with the filtered data
        updated_age_group_survival = filtered_df.groupby('AgeGroup')['Survived'].mean() * 100
        updated_age_group_survival = updated_age_group_survival.reset_index()
        updated_age_group_survival['AgeGroup'] = updated_age_group_survival['AgeGroup'].astype(str)

        # Update the data source
        source.data = ColumnDataSource(updated_age_group_survival).data

        # Update the x_range of the plot to match the new data
        p.x_range.factors = updated_age_group_survival['AgeGroup'].tolist()

    # Attach the update function to the widgets
    class_select.on_change('value', lambda attr, old, new: update())
    gender_select.on_change('value', lambda attr, old, new: update())

    # Arrange the layout
    layout = column(row(class_select, gender_select), p)

    curdoc().add_root(layout)  # Display the plot in a Bokeh server

    output_file(source_path + "/bokeh_plots/age_group_survival.html")  # Specify the output file name
    save(layout)  # Save the layout to the file

    show(layout)   # For Jupyter Notebook or standalone script, use show(layout)







##########Class and Gender: Create a grouped bar chart to compare survival rates across
##########different classes (1st, 2nd, 3rd) and genders (male, female).
# Calculate survival rates
def class_gender(df_survived):
    survival_rates = df_survived.groupby(['Pclass', 'Sex'])['Survived'].mean().unstack().reset_index()
    survival_rates = pd.melt(survival_rates, id_vars=['Pclass'], value_vars=['male', 'female'], var_name='Sex', value_name='Survival_Rate')

    # Prepare data for Bokeh
    survival_rates['Pclass_Sex'] = list(zip(survival_rates['Pclass'].astype(str), survival_rates['Sex']))

    source = ColumnDataSource(survival_rates)

    # Define the factors for x-axis
    factors = [(str(cls), gender) for cls in [1, 2, 3] for gender in ['male', 'female']]

    # Create a figure
    p = figure(x_range=FactorRange(*factors),
            height=400,
            width=700,
            title="Survival Rates by Class and Gender",
            toolbar_location=None,
            tools="")

    # Add bars
    p.vbar(x='Pclass_Sex', top='Survival_Rate', width=0.8, source=source,
        fill_color=factor_cmap('Pclass_Sex', palette=['lightblue', 'lightgreen'], factors=['male', 'female'], start=1, end=2))

    # Add hover tool
    hover = HoverTool()
    hover.tooltips = [
        ("Class", "@Pclass"),
        ("Gender", "@Sex"),
        ("Survival Rate", "@Survival_Rate{0.00%}")
    ]
    p.add_tools(hover)

    # Customize the plot
    p.y_range.start = 0
    p.x_range.range_padding = 0.1
    p.xgrid.grid_line_color = None
    p.yaxis.axis_label = 'Survival Rate'
    p.xaxis.axis_label = 'Class and Gender'
    p.xaxis.major_label_orientation = 1

    # Create filtering widgets
    class_select = Select(title="Passenger Class", value="All", options=["All", "1", "2", "3"])
    gender_select = Select(title="Gender", value="All", options=["All", "male", "female"])

    # Update function to filter data based on selection
    def update():
        selected_class = class_select.value
        selected_gender = gender_select.value

        filtered_df = survival_rates.copy()

        if selected_class != "All":
            filtered_df = filtered_df[filtered_df['Pclass'] == int(selected_class)]
        if selected_gender != "All":
            filtered_df = filtered_df[filtered_df['Sex'] == selected_gender]

        # Update the source data
        source.data = ColumnDataSource(filtered_df).data

        # Update the factors in the x_range to match the filtered data
        new_factors = [(str(cls), gender) for cls, gender in zip(filtered_df['Pclass'], filtered_df['Sex'])]
        p.x_range.factors = new_factors

    # Attach the update function to the widgets
    class_select.on_change('value', lambda attr, old, new: update())
    gender_select.on_change('value', lambda attr, old, new: update())

    layout = column(row(class_select, gender_select), p)   # Arrange the layout

    curdoc().add_root(layout)    # Display the plot in a Bokeh server

    output_file(source_path + "/bokeh_plots/class_gender.html")  # Specify the output file name
    save(layout)  # Save the layout to the file

    show(layout)    # For Jupyter Notebook, use show(layout)








#Fare vs. Survival: Create a scatter plot with Fare on the x-axis and survival status
#on the y-axis, using different colors to represent different classes.
def fare_vs_survival(df_survived):
    # Convert 'Pclass' to str
    df_survived['Pclass'] = df_survived['Pclass'].astype(str)

    # Create a ColumnDataSource
    source = ColumnDataSource(df_survived)

    # Create a color mapping for classes
    color_map = factor_cmap('Pclass', palette=['blue', 'green', 'red'], factors=['1', '2', '3'])

    # Create the figure
    p = figure(width=800, height=400, title="Scatter Plot of Fare vs Survival Status by Class",
            x_axis_label="Fare", y_axis_label="Survived", tools="pan,box_zoom,reset,save")

    # Add the scatter plot
    p.scatter(x='Fare', y='Survived', size=10, color=color_map, legend_field='Pclass', source=source, fill_alpha=0.4)

    # Add hover tool
    hover = HoverTool()
    hover.tooltips = [
        ("Passenger Class", "@Pclass"),
        ("Fare", "@Fare{0.2f}"),
        ("Survived", "@Survived"),
        ("Sex", "@Sex"),
        ("Age", "@Age"),
        ("Name", "@Name")
    ]
    p.add_tools(hover)

    p.legend.title = 'Class'
    p.legend.location = 'top_right'

    # Filter function to update data based on user selection
    def update():
        selected_class = class_select.value
        selected_gender = gender_select.value

        filtered_df = df_survived.copy()
        if selected_class != "All":
            filtered_df = filtered_df[filtered_df['Pclass'] == selected_class]
        if selected_gender != "All":
            filtered_df = filtered_df[filtered_df['Sex'] == selected_gender.lower()]

        # Update the source data with filtered data
        source.data = ColumnDataSource(filtered_df).data

    # Create filter widgets
    class_select = Select(title="Passenger Class", value="All", options=["All", "1", "2", "3"])
    gender_select = Select(title="Gender", value="All", options=["All", "Male", "Female"])

    # Call update() when the filter values change
    class_select.on_change('value', lambda attr, old, new: update())
    gender_select.on_change('value', lambda attr, old, new: update())

    # Arrange the layout
    layout = column(row(class_select, gender_select), p)

    curdoc().add_root(layout)      # Display the plot in a Bokeh server

    output_file(source_path + "/bokeh_plots/fare_vs_survival.html")  # Specify the output file name
    save(layout)  # Save the layout to the file

    show(layout)      # For Jupyter Notebook or standalone script, use show(layout)




if __name__ == "__main__":
    prepare_data_for_processing()
    df_survived = prepare_data_for_processing()
    age_group_survival(df_survived)
    class_gender(df_survived)
    fare_vs_survival(df_survived)





