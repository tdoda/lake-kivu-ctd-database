# Lake Kivu CTD Database

## Project Information

The CTD data has been collected by the Lake Kivu Monitoring Program (REMA) since 2008 and by Kivuwatt since 2010, at different locations in Lake Kivu but mostly near the KP1 methane extraction plant (29.242921°E,-1.732214°N) and the Kivuwatt methane extraction plant (29.202352°E,-2.087932°N).  
A special feature in the processing of the CTD data is the implementation of lake level measurements, which are used to adjust the depth values for each CTD to a standard level of 1462 meters above sea level.

Data and scripts are available on the following git repository: https://gitlab.renkulab.io/eawag-surf/lake-kivu-ctd-profiles.git 

More detailed information about the database: see technical report (<font color='red'>*work in progress*</font>).

## Sensors

The CTD probe is an instrument used to measure the conductivity, temperature, and pressure of the lake water (the D stands for "depth," which is closely related to pressure). Some probes provide additional parameters such as dissolved oxygen, turbidity, pH and Chlorophyll-A. The probes used to create this database include Sea&Sun CTDs and Seabird CTDs.


## Installation

- Clone the repository to your local machine using the command: 

 `git clone https://renkulab.io/gitlab/eawag-surf/lake-kivu-ctd-profiles.git`
 
 Note that the repository will be copied to your current working directory.

- Use Python 3 and install the requirements with:

 `pip install -r requirements.txt`

The python version can be checked by running the command `python --version`. In case python is not installed or only an older version of it, it is recommend to install python through the anaconda distribution which can be downloaded [here](https://www.anaconda.com/products/individual). 

You can also install each package separately:
- conda install netCDF4
- conda install pandas
- conda install dateparser
- pip install envass
- conda install scipy
- pip install seawater
- conda install matplotlib
- pip install gsw
- conda install numpy
- pip install python-dateutil
- pip install PyYAML

## Usage

### Access the database
The final, depth-interpolated and quality checked database is available in two different folders depending on the type of files that the user wants to access:
- one file per CTD profile: folder `data\Level2B`, one netCDF and one CSV file per profile, for REMA and Kivuwatt separately (the profiling date is indicated in the file name).
- one file combing all CTD profiles: folder `data\Level3`, one netCDF for the entire database and one CSV file per variable, from the (i) REMA database, (ii) Kivuwatt database and (iii) combined REMA-Kivuwatt database.

See part ["Folder Data"](#folder-data) for more information.

### Visualize the database

With jupyter notebook: <font color='red'>*work in progress*</font>

The data will be available for visualization on the following website (<font color='red'>*work in progress*</font>): https://www.datalakes-eawag.ch/datadetail/964.

### Process new data

<font color='red'>*Work in progress*</font>

## Organization of the repository
### Folder `data`

The data is structured with the following subfolders:

- `Level0`: Raw CTD data collected by REMA and Kivuwatt (*.TOB, *.cnv, *.hex, *.xslx, *.csv files).

- `Level2A`: Data stored in netCDF and CSV files, where attributes (e.g., units, description of data, etc.), additional quntities (e.g, water density, salinity, depth, etc.) and quality flags are added. Quality flag "1" indicates that the data point did not pass the quality checks and further investigation is needed, quality flag "0" indicates that no further investigation is needed. Each netCDF and CSV file corresponds to a profile, with the profiling date indicated in the file name.

- `Level2B`: Similar data as Level 2A, except that the profiles have been vertically interpolated to a grid of 0.2 m spacing and that the quality flags have been applied to filter the data.

- `Level3`: Final database combining all the profiles from REMA, Kivuwatt and both ("combined database"). The data is stored as a single netCDF file containing all the L2B profiles and as CSV files (one per variable).

- `lake_level`: Contains three different sources of lake level measurements for lake Kivu:
1) **dahit**: Offers continuous measurements with about two measurements per month from 2002-08 until 2021-08. However there is a gap of measurements from 2010-09 until 2013-04.
2) **In-situ (SNEL, Bukavu)**: Has the longest range of measurements from 1941 to 2022-05. Also shows highest density of measurements with monthly measurements from 1941 to 2008 and daily measuremnts from 2008 until 2022-05. The data is not updated regularly but offers the highest quality at the moment.
3) **CGLS**: Offers continuous satellite estimates with about one measurement every two months from 1995 to 2022-11. Updated on a regular base.

- `meta_data`: Csv and Excel files containing the metadata.

- `gas_profile`: Vertical concentration profile of methane and carbon dioxide measured in Lake Kivu in 2018. More information in the publication: Bärenbold F, Boehrer B, Grilli R, Mugisha A, von Tümpling W, Umutoni A, et al. (2020) No increasing risk of a limnic eruption at Lake Kivu: Intercomparison study reveals gas concentrations close to steady state. PLoS ONE 15(8): e0237836. https://doi.org/10.1371/journal.pone.0237836. 

### Folder `scripts`
<font color='red'>*Work in progress*</font>\

### Folder `notebooks`
<font color='red'>*Work in progress*</font>\

### Folder `support_scripts`
<font color='red'>*Work in progress*</font>\
There are 4 support scripts available to visualize the data and add new meta data. They can be found in the folder `support_scripts`. The data is structured as follows:

- **adding_meta_data.py**: Adds meta data from `../data/meta_data/All_CTD_Meta_data.csv` to the raw data in `level0`. If new meta data is available, add it to `All_CTD_Meta_data.csv` and run `adding_meta_data.py`.

- **lake_level_plot**: A simple plot of the three lake level sources.

- **NetCDF_gridded_reader**: A heatmap of the gridded `level2B`data.

- **NetCDF_reader**: Plots meta data and multiple variables of `level2A` data.

### Additional files 

<font color='red'>*Work in progress*</font>

## Quality assurance

Quality checks include but are not limited to range validation, data type checking and flagging missing data. Check

## Contact information

This database is the result of a collaboration between REMA, Kivuwatt and Eawag. The contact people at Eawag are Martin Schmid (martin.schmid@eawag.ch) and Tomy Doda (tomy.doda@eawag.ch).