# France Immigration & Election (Extreme Right Votes) Dashboard

**Live App → [extreme-right-election-map.streamlit.app](https://extreme-right-election-map.streamlit.app/)**

I created an interactive data dashboard to explore the geographic distribution of residents born non-French and the extreme-right voting patterns across France (built with Python and Streamlit).

---

## My motivation behind this project

This project was born out of a growing concern over the rise of the extreme right in France and an increase in xenophobic discourse in the media. This idea was sparked after reading about research in **contact theory**, i.e, the hypothesis that people with less exposure to social diversity are more likely to hold prejudiced views build by the extreme-right wing-affiliated media and vote for far-right parties. In particular, an article by Le Monde, [La figure de l'étranger, ce repoussoir imaginaire](https://www.lemonde.fr/idees/article/2023/11/17/la-figure-de-l-etranger-ce-repoussoir-imaginaire_6200771_3232.html) (November 2023) (English: the figure of the foreigner as an imaginary repellent) , titled: "The National Rally achieves its highest vote shares in rural and suburban areas where there are few foreigners. For these voters, voting for the National Rally is not driven by a negative experience of diversity, but by a desire for social respectability. Their aim is to distinguish themselves from those on benefits, a category into which they place immigrants."

The data, which can be visualised on the interactive dashboard, seems to support this: areas with lower non-French-born population ratios tend to show higher support for right-wing parties, while more diverse urban areas lean further left. This dashboard was built to make that pattern visible and explorable at both the département and communes level. In-depth studies attempted to show that even when accounting for the votes of second- and third-generation immigrants this pattern holds.

### References & Further Reading

- [La figure de l'étranger, ce repoussoir imaginaire](https://www.lemonde.fr/idees/article/2023/11/17/la-figure-de-l-etranger-ce-repoussoir-imaginaire_6200771_3232.html) — *Le Monde*, November 2023
- [Les ressorts cachés du RN : sociologie du vote d'extrême droite](https://conference.sciencespo.fr/content/2024-10-16/les-ressorts-caches-du-rn-sociologie-du-vote-d-extreme-droite_6rajXggaUDbyw7QwuEjl) — Sciences Po, October 2024
- [Pour qui votent les descendants d'émigrés en France](https://www.revueconflits.com/pour-qui-votent-les-descendants-demigres-en-france/) - Revue Conflit, 2020

---

## What the Dashboard Shows

### Tab 1 — Immigration Statistics
- Percentage of immigrants (born outside France) per département or commune
- Filterable by year (2018–2021) and geographic scale
- Ranked table of areas with the highest immigrant population share
- Data source: INSEE — Recensement de la population [IMG1A]

### Tab 2 — 2022 Presidential Election Results
- Percentage of votes cast for extreme-right candidates (Le Pen, Zemmour, Dupont-Aignan) per département or commune
- Filterable by round (First / Second) and geographic scale
- Commune-level detail available for the First Round; département level for the Second Round
- Data source: Kaggle — [Premier Tour](https://www.kaggle.com/datasets/clementh7/election-presidentielle-premier-tour-2022) / [Deuxième Tour](https://www.kaggle.com/datasets/clementh7/election-presidentielle-deuxime-tour-2022)

---

## Project Structure

```
├── dashboard.py        # Main Streamlit app
├── requirements.txt    # Python dependencies
└── README.md
```

---

## Data Sources

- **Immigration data**: [INSEE — Nationalité et Immigration, Recensement de la population IMG1A](https://www.insee.fr/fr/statistiques/8202714?sommaire=8202756#consulter)
- **Election data (Round 1)**: [Kaggle — clementh7/election-presidentielle-premier-tour-2022](https://www.kaggle.com/datasets/clementh7/election-presidentielle-premier-tour-2022)
- **Election data (Round 2)**: [Kaggle — clementh7/election-presidentielle-deuxime-tour-2022](https://www.kaggle.com/datasets/clementh7/election-presidentielle-deuxime-tour-2022)
- **GeoJSON boundaries**: [gregoiredavid/france-geojson](https://github.com/gregoiredavid/france-geojson)

---

## Notes

- According to the INSEE definition, an **immigrant** is a person born outside France, regardless of current nationality. The status is permanent — it does not change if the person later acquires French citizenship.
- The extreme-right political group in this dashboard includes candidates classified as *extrême droite*: Le Pen, Zemmour, and Dupont-Aignan.
- Commune-level election data is only available for the First Round due to dataset limitations for the Second Round.
