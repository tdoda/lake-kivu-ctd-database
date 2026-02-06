# Lake Kivu CTD Database

## Project Information

The CTD data has been collected by the Lake Kivu Monitoring Program (REMA) since 2008 and by Kivuwatt since 2010, at different locations in Lake Kivu but mostly near the KP1 methane extraction plant (29.242921°E,-1.732214°N) and the Kivuwatt methane extraction plant (29.202352°E,-2.087932°N).  
A special feature in the processing of the CTD data is the implementation of lake level measurements, which are used to adjust the depth values for each CTD to a standard level of 1462 meters above sea level.

Data and scripts are available on the following git repository: https://github.com/tdoda/lake-kivu-ctd-database.git 

More detailed information about the database: see technical report (<font color='red'>*work in progress*</font>).

## Sensors

The CTD probe is an instrument used to measure the conductivity, temperature, and pressure of the lake water (the D stands for "depth," which is closely related to pressure). Some probes provide additional parameters such as dissolved oxygen, turbidity, pH and Chlorophyll-A. The probes used to create this database include Sea&Sun CTDs and Seabird CTDs.


## Installation

### 1. Python installation

Python 3 is required to run the scripts. Three installation are possible:
- Recommended option: download [Miniforge](https://github.com/conda-forge/miniforge). 
- User-friendly option: download the [Anaconda distribution](https://www.anaconda.com/products/individual).
- Classic option: download Python from the [official website](https://www.python.org/downloads/).

### 2. Repository installation

- If using GIT, clone the repository to your local machine using the command in Git Bash: 

    ``` 
    git clone https://github.com/tdoda/lake-kivu-ctd-database.git 
    ```
 
    Note that the repository will be copied to your current working directory.
- Without GIT, just download the entire ZIP folder from https://github.com/tdoda/lake-kivu-ctd-database.git ("Code" > "Download ZIP") and extract it.

### 3. Packages installation

1. Open the terminal (e.g., Anaconda Prompt), and move to the `lake-kivu-ctd-database` repository.
2. Create a new environment *kivu-ctd* and install the packages as follows:
    - If using conda (Anaconda or Miniforge installation):
        ```
        conda env create -f environment.yml
        conda activate kivu-ctd 
        ```
        It is also possible to install the packages from `requirements.txt` with pip instead:
        ```
        conda create -n kivu-ctd python=3.11
        conda activate kivu-ctd
        pip install -r requirements.txt
        ```
    - If using mamba (Anaconda or Miniforge installation):
        ```
        mamba env create -f environment.yml
        mamba activate kivu-ctd 
        ```
    - If using pip (classic Python installation):
        ```
        python -m venv kivu-ctd       
        source kivu-ctd /bin/activate  # For Linux/macOS
        kivu-ctd\Scripts\activate     # For Windows
        pip install -r requirements.txt
        ```

## Working with the project online without any installation (Renku)

<font color='red'>*To be tested*</font>

## Usage

The CTD database is stored in the `data\ctd` folder. The datafiles cannot be uploaded to Github, but can be accessed, downloaded and uploaded on [this One Drive repository](https://unils-my.sharepoint.com/:f:/g/personal/tomy_doda_unil_ch/IgA6OpMf4csFTr5knuORmeJCAZ4UavAgWEneRdtgZn8CDlA?e=6J5zUS). 

### Access the database
The final, depth-interpolated and quality checked database is available in two different folders depending on the type of files that the user wants to access:
- One file per CTD profile in folder `data\ctd\Level2B`: one netCDF and one CSV file per profile, for REMA (`data\ctd\Level2B\REMA`) and Kivuwatt (`data\ctd\Level2B\Kivuwatt`). The profiling date is indicated in the file name.
- One file combing all CTD profiles in folder `data\ctd\Level3`: one netCDF for the entire database and one CSV file per variable, from the (i) REMA database (`data\ctd\Level3\REMA`), (ii) Kivuwatt database (`data\ctd\Level3\Kivuwatt`) and (iii) combined REMA-Kivuwatt database (`data\ctd\Level3\Combined`).

See the section [`Folder Data`](#folder-data) for more information.

### Visualize the database

With jupyter notebook: <font color='red'>*work in progress*</font>

The data will be available for visualization on the following website (<font color='red'>*work in progress*</font>): https://www.datalakes-eawag.ch/datadetail/964.

### Process new data

The current version of the database is only able to process .TOB and .cnv data files from REMA and .csv files from Kivuwatt. The steps to follow to process new data are described below.

#### 1. Store new data
Add new REMA data files in the folder `data\ctd\Level0\REMA` and new Kivuwatt data files in the folder `data\ctd\Level0\Kivuwatt`. 

To store the data at another location, you need to spoecify the path to the folders in the file `scripts\input_python.yaml` as `Level0_dir` (REMA) and `Level0_KW_dir` (Kivuwatt). You can also specify in the same file where the Level2A, Level2B and Level3 folders should be created, if not existing already.

#### 2A. Launch data processing without opening the scripts (easy option) 

1. Locate the location of the installed `python.exe` for the *kivu-ctd* environment by typing 
    ```
    where python
    ```
    in the terminal (e.g., Anaconda prompt) with the *kivu-ctd* environment activated.
2. Copy the path and paste it in the file `python_path.txt`.
3. Run the script by double clicking on `process_database.bat`. A terminal should open showing
    ```
    Active code page: 65001
    Starting data processing
    Please wait until the Processing Options window opens...
    ```
    Wait for a few seconds until the *Processing Options* window opens.
4. In the *Processing Options* window, you can select the following options:
    - *Data type*: "REMA" and/or "Kivuwatt" (at least one of the two options is required).
    - *Processing level*: "Level 0 → Level 2" and/or "Level 2 → Level 3" (at least one of the two options is required).
    - *Save CSV files in addition to netCDF files*: select it to save L2 and L3 data as .csv files in addition to .nc files.
    - *Show output in the terminal*: select it to display detailed information about each processing step in the terminal (useful for debugging, but takes more time).
    
    Then click on *OK*.
5. Selection windows will open in the following cases:
    - If the option "Level 0 → Level 2" was selected, a selection window will open to select the Level0 files to process (separate windows for REMA and Kivuwatt files). These files will be automatically converted to Level3 files if "Level 2 → Level 3" was also selected.
    - If the option "Level 2 → Level 3" was selected **without** "Level 0 → Level 2" and **with** existing Level 3 files, a selection window will open to select the Level2B files to process.

    Note that if Level3 files do not exist yet, **all existing Level2B files** will be automatically converted to Level3 files, including Level2B files not corresponding to the chosen Level0 files, as long as "Level 2 → Level 3" was selected. 

#### 2B. Launch data processing by using the Python script (advanced option) 

1. Open `scripts\main_ctd_database.py` in a Python IDE (e.g., Spyder, VS Code).
2. Run the script directly to use the GUI windows (follow steps 4-5 from [Option 2A](#2a-launch-data-processing-without-opening-the-scripts-easy-option)). You can also modify the parameters manually as follows:
    - In the section *Choices for the database creation*, comment the part 
        ```
        # With GUI:
        options = select_processing_options(process_REMA=True, process_KW=True,process_L0toL2=True,process_L2toL3=True,save_csv=True,show_output=False)
        process_REMA    = options["process_REMA"]
        process_KW      = options["process_KW"]
        show_output     = options["show_output"]
        save_csv        = options["save_csv"]
        process_L0toL2  = options["process_L0toL2"]
        process_L2toL3  = options["process_L2toL3"]
        ```
        and uncomment the part below 
        ```
        # Manually
        ```
        - Specify which data type you want to process:
            ```
            process_REMA    = True # To process REMA data
            process_KW      = True # To process Kivuwatt data
            ```
        - Specify the processing steps to perform (from Level 0 to Level 2 only, from Level 2 to Level 3 only, or both steps):
            ```
            process_L0toL2=True # To process Level 0 to Level 2
            process_L2toL3=True # To process Level 2 to Level 3
            ```
        - To display detailed information about each processing step in the terminal (useful for debugging, but takes more time), use:
            ```
            show_output=True
            ```
        - To save data as .csv files in addition to .nc files, use:
            ```
            save_csv=True
            ```
    - In the Section *Parameters*, comment the part 
        ```
        # Use GUI to select new files to process:
        if process_REMA:
            files_REMA = select_files(dirname=directories["Level0_dir"],messagestr="Select REMA CTD files to process",filetypes=(("REMA files", "*.TOB *.cnv"),))
        else:
            files_REMA = []
        if process_KW:
            files_KW = select_files(dirname=directories["Level0_KW_dir"],messagestr="Select Kivuwatt CTD files to process",filetypes=(("KW files", "*.csv"),))
        else:
            files_KW = []
        ```
        Select Level 0 files to export, with one of the two following methods:
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

#### 3. Track the data processing steps  

The progress can be tracked in the terminal, with the name of each file that is processed. 

The selected Level0 files (if any) are exported to Level2A (`data\ctd\Level2A`) and Level2B (`data\ctd\Level2B`), except if they were already exported. If Level3 files (`data\ctd\Level3`) do not exist, they are created from all the existing Level3B files. If Level3 files already exist, the selected Level2B files (if any) are added to the existing Level3 files, except if they were already included. The combined Level3 database (`data\ctd\Level3\Combined`) is created only if there are already Level2B files from REMA and Kivuwatt.

In case some of the data files cannot be read (e.g., wrong format), those files will be skipped and their names will be saved in the file `data\ctd\files_removed.txt`, with some information about the error source. More detailed information about the location of the error is displayed in the Python terminal if the option *Show output in the terminal* was selected.

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

This database is the result of a collaboration between REMA, Kivuwatt and Eawag. The contact people at Eawag are Martin Schmid (martin.schmid@eawag.ch), Tomy Doda (tomy.doda@eawag.ch) and Jean Modeste Mushimiyimana (jeanmodeste.mushimiyimana@eawag.ch).