# checkra_website

This is the front end for my Checkra Podcast aggregator project, developed using Flask, and Plotly-dash for visualizations. [Available Here](https://checkra.co)

The setup was somewhat complicated as I heavily used Plotly but did not want to pay the full version.

I followed the process [here](https://hackersandslackers.com/plotly-dash-with-flask/), so page had to embed a smaller instance of Dash. Actual implementations in src folder

The technical development was straight forward:
- [Podcasts Page](https://checkra.co/podcasts)
  - Queried data for the appropriate podcast from Mongo
  - Summary: extracted the most important sentences using Term-frequency 
  - Timestamps: Using previously calculated Numpy array of topics, created a multi-line graph 
  - Wordcloud: Generated PNG using matplotlib of highest frequency terms in the section of the podcast
- [Graphs Page](https://checkra.co/graphs)
  - Still a lot of work to do here, but can choose a specific keyword, and a list of closely related podcasts are returned
