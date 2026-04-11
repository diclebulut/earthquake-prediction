# earthquake-prediction
This project takes earthquake data from Turkey and runs analysis for predictions.

- Earthquake data is taken from Boğaziçi University Kandilli Observatory and Earthquake Research Institute Regional Earthquake-Tsunami Monitoring and Evaluation Center http://www.koeri.boun.edu.tr/scripts/lst8.asp 
- Data download script is taken from user melihme: https://gist.github.com/melihme/cb5769c8b9683ff5a1b6849c56adbdc6
- Global faults geojson data is taken from GEM Global Active Faults Database (GEM GAF-DB) https://github.com/GEMScienceTools/gem-global-active-faults?tab=readme-ov-file
- More research regarding faults database can be found here: Styron R, Pagani M. The GEM Global Active Faults Database. Earthquake Spectra. 2020;36(1_suppl):160-180. doi:10.1177/8755293020944182


## Run Instructions
- Using Poetry (recommended):
	1. Install Poetry: https://python-poetry.org/docs/#installation
	2. From project root, install dependencies: `poetry install`
	3. Start a Poetry shell: `poetry shell`
	4. Launch VS Code or Jupyter and select the Poetry environment kernel

- Legacy pip setup:
	- Analysis notebook could be ran on VSCode or equivalent by creating a .venv and installing the requirements in requirements.txt
  
