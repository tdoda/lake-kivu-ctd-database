# Lake Kivu CTD Database

## Project Information

The CTD data has been collected by the Lake Kivu Monitoring Program (REMA) since 2008 and by Kivuwatt since 2010, at different locations in Lake Kivu but mostly near the KP1 methane extraction plant (29.242921°E,-1.732214°N) and the Kivuwatt methane extraction plant (29.202352°E,-2.087932°N).  
A special feature in the processing of the CTD data is the implementation of lake level measurements, which are used to adjust the depth values for each CTD to a standard level of 1462 meters above sea level.

Data and scripts are available on the following git repository: https://github.com/tdoda/lake-kivu-ctd-database.git 

More detailed information about the database: see technical report (<font color='red'>*work in progress*</font>).

## Sensors

The CTD probe is an instrument used to measure the conductivity, temperature, and pressure of the lake water (the D stands for "depth," which is closely related to pressure). Some probes provide additional parameters such as dissolved oxygen, turbidity, pH and Chlorophyll-A. The probes used to create this database include Sea&Sun CTDs and Seabird CTDs.


## Installation

- Clone the repository to your local machine using the command: 

 `git clone https://github.com/tdoda/lake-kivu-ctd-database.git`
 
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

The CTD database is stored in the `data\ctd` folder. The datafiles cannot be uploaded to Github, but can be accessed, downloaded and uploaded on [this One Drive repository](https://unils-my.sharepoint.com/:f:/g/personal/tomy_doda_unil_ch/IgA6OpMf4csFTr5knuORmeJCAZ4UavAgWEneRdtgZn8CDlA?e=6J5zUS). 

### Access the database
The final, depth-interpolated and quality checked database is available in two different folders depending on the type of files that the user wants to access:
- one file per CTD profile: folder `data\ctd\Level2B`, one netCDF and one CSV file per profile, for REMA and Kivuwatt separately (the profiling date is indicated in the file name).
- one file combing all CTD profiles: folder `data\ctd\Level3`, one netCDF for the entire database and one CSV file per variable, from the (i) REMA database, (ii) Kivuwatt database and (iii) combined REMA-Kivuwatt database.

See part [`Folder Data`](#folder-data) for more information.

### Visualize the database

With jupyter notebook: <font color='red'>*work in progress*</font>

The data will be available for visualization on the following website (<font color='red'>*work in progress*</font>): https://www.datalakes-eawag.ch/datadetail/964.

### Process new data

The current version of the database is only able to process .TOB and .cnv data files from REMA and .csv files from Kivuwatt. The steps to follow to process new data are:
1. Add the new files in the folder `data\ctd\Level0\REMA` (or in a separate folder that should be specified as `Level0_dir` in the file `scripts\input_python.yaml`). You can also specify in `scripts\input_python.yaml` where the Level2 and Level3 folders should be created, if not existing already.
2. In `scripts\main_ctd_database.py`, modify the *Parameters* section as followed:
    - Specify which data processing steps should be performed (from Level 0 to Level 2 only, from Level 2 to Level 3 only, or both steps):
        ```
        process_L0toL2=True # To process Level 0 to Level 2
        process_L2toL3=True # To process Level 2 to Level 3
        ```
        - Processing from Level 0 to Level 2: only done for the selected files (see below), if they were not exported to Level 2 yet 
        - Processing from Level 2 to Level 3: if Level 3 files do not exist yet, all Level 2 files are exported to Level 3; if level 3 files already exist, only the Level 2 files from selected Level 0 files (see below) are exported to Level 3.   
    - To display detailed information on each data file processing in the Python command (useful for debugging, but takes more time), use:
        ```
        show_output=True
        ```
    - To save data as .csv files in addition to .nc files, use:
        ```
        save_csv=True
        ```
    - Select Level 0 files to export, with one of the three following methods:
        - Interactively with a GUI interface (requires the tkinter package):
            ```
            # Use GUI to select new files to process (requires tkinter):
            files_REMA = select_files(dirname=directories["Level0_dir"],messagestr="Select REMA CTD files to process",filetypes=(("REMA files", "*.TOB *.cnv"),))

            files_KW = select_files(dirname=directories["Level0_KW_dir"],messagestr="Select Kivuwatt CTD files to process",filetypes=(("KW files", "*.csv"),))
            ```
        - By specifying filenames in the lists `files_REMA` and `files_KW`. Example: 
            ```
            files_REMA = ['0000.TOB','0001.TOB']

            files_KW = ['Data1.csv']
            ```
        - By processing all Level 0 data files:
            ```
            files_REMA=[f for f in os.listdir(directories["Level0_dir"]) if f.endswith((".TOB",".cnv"))]

            files_KW=[f for f in os.listdir(directories["Level0_KW_dir"]) if f.endswith((".csv")) and f.startswith('D')]
            ```
        Make sure that the new profiles were taken after `min_date_period`. If not, change the date of `min_date_period` with the format `datetime(yyyy,mm,dd)`. For example:
        ```
        min_date_period=datetime(2001, 1, 1) # 1st January 2001
        ```
3. Run the script `scripts\main_ctd_database.py`: new L2A and L2B files corresponding the new profiles should be added to the folders `data\ctd\Level2A` and `data\ctd\Level2B` and L3 files in folder `data\ctd\Level3` should be replaced by the new database containing the new files. 

    In case some of the data files cannot be read (e.g., wrong format), those files will be skipped and their names will be saved in the file `data\ctd\files_removed.txt`, with some information about the error source. More detailed information about the location of the error is displayed in the Python terminal if 
    ```
    show_output=True
    ``` 
    in `scripts\main_ctd_database.py`.



## Organization of the repository
### Folder `data`

The data is structured with the following subfolders:

- `ctd`: CTD database, not stored on Github but accessible on [this OneDrive repository](https://unils-my.sharepoint.com/:f:/g/personal/tomy_doda_unil_ch/IgA6OpMf4csFTr5knuORmeJCAZ4UavAgWEneRdtgZn8CDlA?e=6J5zUS). The CTD data is organized into the following subfolders:
    - `Level0`: Raw CTD data collected by REMA and Kivuwatt (*.TOB, *.cnv, *.hex, *.xslx, *.csv files).
    - `Level2A`: Data stored in netCDF and CSV files, where attributes (e.g., units, description of data, etc.), additional quantities (e.g, water density, salinity, depth, etc.) and quality flags are added. Quality flag "1" indicates that the data point did not pass the quality checks and further investigation is needed, quality flag "0" indicates that no further investigation is needed. Each netCDF and CSV file corresponds to a profile, with the profiling date indicated in the file name.
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