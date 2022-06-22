# Lake Kivu CTD

## Project Information

The CTD data is collected within the Lake Kivu Monitoring Program. A special feature in the processing of the CTD data for lake Kivu is the implementation of lake level measurements, which are used to adjust the depth values for each CTD to a standard level of 1462 meters above sea level. 


## Sensors

The CTD is an instrument used to measure the conductivity, temperature, and pressure of the lake water (the D stands for "depth," which is closely related to pressure).


## Installation

- Clone the repository to your local machine using the command: 

 `git clone https://renkulab.io/gitlab/lexplore/ctd.git`
 
 Note that the repository will be copied to your current working directory.

- Use Python 3 and install the requirements with:

 `pip install -r requirements.txt`

 The python version can be checked by running the command `python --version`. In case python is not installed or only an older version of it, it is recommend to install python through the anaconda distribution which can be downloaded [here](https://www.anaconda.com/products/individual). 


## Usage


### Process new data

In order to process new data locally on your machine the file path needs to be adapted to your local file system. The following steps are therefore necessary: 

- Edit the `scripts/input_batch.bat` file. Change all the directory paths to match your local file system. This file contains all the file paths necessary to launch the batch scripts `runfile.bat`.

- Edit the `scripts/input_python.py` file. Change all the directory paths to match your local file system. This file contains all the directories where the python script outputs data to.

To process new data, place the data in the input directory which you specified in the `scripts/input_batch.bat` file. 
Double-clicking on the `runfile.bat` file will automaticall process all the data in the input directory and store the output 
in the directories specified in the `scripts/input_python.py` file. Note that the input files need to have the same 
directory structure as the already exisiting files in the `data/Level 0` folder. 


### Adapt/Extend data processing piepeline

The python script `scripts/main_ctd.py` defines the different processing steps while the python script `scripts/ctd.py` contains the python class thetis with all the corresponding 
class methods to process the data. To add a new processing or visualization step, a new class method can be created in the `ctd.py` file and the step can be added in `main_ctd.py` file.
Both above mentioned python scripts are independent of the local file system.


### Visualize Data/ Add new meta Data

There are 4 support scripts available to visualize the data and add new meta data. They be found in the folder `support_scripts`. The data is structured as follows:

- **adding_meta_data.py**: Adds meta data from `../data/meta_data/All_CTD_Meta_data.csv` to the raw data in `level0`. If new meta data is available, add it to `All_CTD_Meta_data.csv` and run `adding_meta_data.py`.

- **lake_level_plot**: A simple plot of the three lake level sources.

- **NetCDF_gridded_reader**: A heatmap of the gridded `level2B`data.

- **NetCDF_reader**: Plots meta data and multiple variables of `level2A` data.


## Data

The data can be found in the folder `data`. The data is structured as follows:


### Data Structure

- **Level 0**: Raw data collected from the different sensors.

- **Level 1**: Raw data stored to NetCDF file where attributes (such as sensors used, units, description of data, etc.) are added to the data.

- **Level 2A**: Column with quality flags are added to the Level 1A data. Quality flag "1" indicates that the data point didn't pass the 
quality checks and further investigation is needed, quality flag "0" indicates that no further investiagion is needed.

- **Level 2B**: The profile is vertically gridded with a vertical spacing of 0.5m and the "Thrope Lengthscale" as well as the "Vertical diffusivity" are calculated. 
The data is stored to a NetCDF file spanning over a time period one year.

	**Note** that the filename of level 1, level 2A and level 2B show the date of the profile.

- **lake_level**: Contains three different sources of lake level measurements for lake Kivu:
-- DAHITI: Offers continuous measurements with about two measurements per month from 2002-08 until 2021-08. However theres a gap of measurements from 2010-09 until 2013-04
-- In-situ (SNEL, Bukavu): Has the longest range of measurements starting 1941 until 2022-05. Alos shows highest density of measurements with monthly measurements from 1941 to 2008 and daily measuremnts from 2008 until 2022-05. The data is not updated regularly but offers the highest quality at the moment.
-- CGLS: Offers continuous measurements with about one measurement every two months from 1995 until 2022-02. Updated on a regular base.

- **meta_data**: A csv.-file with all meta data up to now (21.06.2022).


## Quality assurance

Quality checks include but are not limited to range validation, data type checking and flagging missing data.
