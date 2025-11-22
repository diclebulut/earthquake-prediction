


Creating virtual environment
1. Use the Python: Create Environment command to create a new Python virtual environment.

>Python: Create Environment...

2. Select Venv from the environment type options.

3. Choose the Python interpreter to use as the base for your virtual environment.

4. Wait for the environment creation to complete. A notification will show the progress.

5. Once created, select the new environment by using the Python: Select Interpreter command.

>Python: Select Interpreter


6. Open the integrated terminal using Ctrl + `  (or View: Toggle Integrated Terminal command).

7. Install packages using pip by running commands like:

pip install package_name for a single package
pip install -r requirements.txt for multiple packages from a requirements file






## Description of the analysis problem

- Earthquakes happening near one fault line affect the probability of further earthquake instances near the same fault.

- More recent earthquakes affect the probability of further earthquake instances more than less recent earthquakes.

- Earthquakes happening near a fault could affect the probability of further earthquake instances near faults around the initially affected faults.

- Depth of earthquakes near a fault line can vary but it could affect the probability of further earthquake instances and their depth. 

- Faults change state every time an earthquake happens and they contain those earthquake's effects. They are geographical features that get changed with happenings of earthquakes. 

- Lower magnitude earthquakes happen more often than higher magnitude earthquakes. 

- The scale for measuring earthquake magnitudes (appears as magnitude in the data), developed in 1935 by Charles F. Richter and popularly known as the "Richter" scale, is actually the local magnitude scale, label ML or ML. (https://en.wikipedia.org/wiki/Seismic_magnitude_scales)

- The the scale is logarithmic, so that each unit represents a ten-fold increase in the amplitude of the seismic waves. As the energy of a wave is proportional to A1.5, where A denotes the amplitude, each unit of magnitude represents a 101.5 ≈ 32-fold increase in the seismic energy (strength) of an earthquake.

- Fault dip (appears as average_dip in the data) plays a crucial role in determining how stress accumulates along a fault line. A steeper dip can lead to more vertical movement during an earthquake, which may result in more intense shaking. By analyzing the dip of faults in a region, geologists can better assess seismic hazards and identify areas that may be at higher risk for significant earthquake activity. (Fiveable. "fault dip – Intro to Geology." Edited by Becky Bahr, Fiveable, 2024, https://fiveable.me/key-terms/introduction-geology/fault-dip. Accessed 19 Nov. 2025.)

- Earthquakes contribute to dissipating the energy accumulated in the brittle lithosphere due to the tectonic stress arising from the motion of contiguous crustal volumes with respect to each other. Thrust faulting, usually featured by angles of dip ranging in between 5°−30°, mostly occurs along the margins of plates, where their motions induce elastic strain accumulation, which is released by multifaceted fault slip dynamics ranging from almost periodic silent events to megathrust earthquakes1. 
Zaccagnino, D., Doglioni, C. The impact of faulting complexity and type on earthquake rupture dynamics. Commun Earth Environ 3, 258 (2022). https://doi.org/10.1038/s43247-022-00593-5

- Strike-slip-faulting earthquakes are localized along steeply dipping faults (70°−90°) or transcurrent plate boundaries and transfer zones, while normal faults develop along rift zones in extensional regimes having intermediate dip (45°−65°).
Zaccagnino, D., Doglioni, C. The impact of faulting complexity and type on earthquake rupture dynamics. Commun Earth Environ 3, 258 (2022). https://doi.org/10.1038/s43247-022-00593-5

-  The three major fault types (appears as slip_type in the data) e.g. reverse dip-slip (reverse faults that dip at  shallow  angles  ~<45º  are  called thrusts), normal dip-slip and strike-slip are  described  by  their  corresponding focal mechanisms, providing the values of these three angles, e.g. the strike, the dip and the rake.
Kiratzi, Anastasia. (2014). Mechanisms of Earthquakes in Aegean. 10.1007/978-3-642-36197-5_299-1. 


The main objective of a machine learning model is taking all these into account, discerning previous patterns in areas, taking into account the states of faults according to previously occured earthquakes, earthquake depths, fault average_dips, average_rakes etc and calculating possible future occurances with probabilities and locations. 


## Questions
- Is the existing data enough for this analysis?
- Since faults change state every time an earthquake happens around them, what kind of pattern finding method could be utilised? 


## Data
- Earthquake data is taken from Boğaziçi University Kandilli Observatory and Earthquake Research Institute Regional Earthquake-Tsunami Monitoring and Evaluation Center http://www.koeri.boun.edu.tr/scripts/lst8.asp 
- Data download script is taken from user melihme: https://gist.github.com/melihme/cb5769c8b9683ff5a1b6849c56adbdc6
- Global faults geojson data is taken from GEM Global Active Faults Database (GEM GAF-DB) https://github.com/GEMScienceTools/gem-global-active-faults?tab=readme-ov-file
- More research regarding faults database can be found here: Styron R, Pagani M. The GEM Global Active Faults Database. Earthquake Spectra. 2020;36(1_suppl):160-180. doi:10.1177/8755293020944182

Data fields are as follows at data exploration stage:
- timestamp: this is not parsed 
- location: region and city 
- magnitude: local magnitude scale ML 
- latitude
- longitude
- depth: km
- city: as extracted from location
- closest_fault_idx: fault index
- distance_to_fault: in degrees
- catalog_id: Catalog name of the fault
- slip_type: fault type (Normal, Dextral-Normal, Sinistral, Dextral, Subduction_Thrust, Sinistral-Normal)
- fault_coordinates
- average_dip
- average_rake
- lower_seis_depth
- net_slip_rate
- upper_seis_depth
- distance_to_fault_m: in meters
- distance_to_fault_km: in km
- timestamp_dt: parsed

### Removed Columns
- catalog_name: which catalog it comes from
- geometry_type: all LineString or None

#### Not populated enough
- epistemic_quality: populated across multiple slip types
- activity_confidence: only populated in non Normal slip types
- shortening_rate: only populated in Subduction_Thrust
- strike_slip_rate: only populated in Subduction_Thrust

### Data Manipulation Notes

#### Rake, slip and dip rates: tuple to single int justification: 

The tuple has the format (most-likely, min, max). In some instances where there is no estimated uncertainty in the parameter of interest, the tuple may be simply given as (most-likely,,); this is most common for the dip of purely strike-slip faults (https://github.com/GEMScienceTools/gem-global-active-faults).

#### Fault Names
EUR_TRCS210 and ME_TRCS210 are about the same coordinates but they have different characteristics. Investigate.


