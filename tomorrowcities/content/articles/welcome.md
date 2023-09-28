---
author: huseyin.kaya
title: Welcome!
description: A Brief Introduction to Tomorrow's Cities Decision Support Environment (TCDSE)
image: https://images.unsplash.com/photo-1429041966141-44d228a42775?ixid=MXwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=2500&q=80
thumbnail: https://images.unsplash.com/photo-1429041966141-44d228a42775?ixid=MXwxMjA3fDB8MHxwaG90by1wYWdlfHx8fGVufDB8fHw%3D&ixlib=rb-1.2.1&auto=format&fit=crop&w=350&q=80
alt: "Welcome!"
createdAt: 2023-10-10
duration: 6 min read
category:
  - general
---

## Tomorrow's Cities Decision Support Environment (TCDSE)
TCDSE is a web application designed to conduct computational tasks to generate information needed for decision mechanisms in designing future cities. The web application, which will be referred as TCDSE for short, contains a computational engine capable of executing several hazard scenarios on different exposure datasets and infrastructures. 

## What is New?
### New policies
* Eight new policies are added. See their definitions [here](/docs/policies)
* New info related to flood damage assessment is added [here](/docs/flood)

### Policy Support
Two new policies are added to the computing engine. More info is [here](/docs/policies)

### Excel support:
You can  upload Excel files containing your tabular data such as individual, household, fragility or vulnerability data. However, processing excel files is very slower than processing JSON files so I definitely suggest working with JSON files. You can convert your Excel files via panda framework. The platform also does not try to convert the coordinates even if there is any in the Excel file because there is no way to know which columns represent the coordinates or coordinate reference systems without metadata. So Excel spreadsheets should be used to provide non-geo related tabular data.  So please use them only for data not containing any geo-specific information. 

### Dar Es Salaam Study
[Sample Dataset](https://drive.google.com/file/d/1BGPZQ2IKJHY9ExOCCHcNNrCTioYZ8D1y/view?usp=sharing) now contains some visioning scenario for Dar Es Salaam case.

## Features
General capabilities/features of the web application can be summarized as follows:


*Hazard Scenarios*

* Earthquake
* Flood
* Debris

*Exposure Scenarios*

* Buildings
* Power networks
* Transportation
* Water networks

*Impact Metrics*

* Building and infrastructure-level damage states
* Household and individual-level derived metrics

*Visualization*

* GIS Maps
* Hazard and Exposure data displayers
* Reactive metric widgets
* Damage state classifications

*Data structure*

* GeoJSON format for geospatial data
* Vanilla JSON for non-geospatioal tabular data

*Software*

* Pure-Python development for both backend and frontend
* Reactive user interface via Solara
* geospatial database via postgis
* Leaflet backend for maps
* Easy deployment to cloud


## Quickstart
* Download [Sample Dataset](https://drive.google.com/file/d/1BGPZQ2IKJHY9ExOCCHcNNrCTioYZ8D1y/view?usp=sharing) to your local environment and unzip the archieve file.
* Go to [engine](/engine)
* Drag/drop necessary files to the drop zone of the engine and execute the engine. A sample session is displayed below. 
* The impact metrics will be immediately seen on the page.

<video width="853" controls>
  <source src="https://github-production-user-asset-6210df.s3.amazonaws.com/2515171/270064030-0733ad34-0a7f-445e-86fb-9a61df4e2969.mp4" type="video/mp4">
</video>

In case the file names in the video are not clearly seen, they are: 

* nairobi_business_buildings.geojson
* nairobi_business_household.json
* nairobi_business_individual.json
* nairobi_earthquake_fragility.json
* nairobi_earthquake_intensity.geojson

The used files above satisfy minimum requirements to run Earthquake analysis on buildings. 