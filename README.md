
# AI-based landing assistant in a simplified aircraft approach simulation

An algorithm that performs descent and landing on optimal flight descent path to the destination airport runway. Based on jsbsim flight physics engine and FlightGear for 3D visualization.




## Environment setting

#### Get required packages with conda

```bash
  conda env create -f environment.yml
```

Recreate the environment landing-ai in VS Code.



## Running 3D visualisation

If you wish to use optional 3D visualisation you need to download the os-corresponding version of [FlightGear flight simulator](https://www.flightgear.org).

FlightGear needs to be running before any Python code. To run it properly use bash script in fg_conf directory:

```bash
  ./fg_conf/fg_run.sh
```

Some of preset runways may require to run FlightGear alone in that airport first in order to download maps. Simply open the FlightGear with main .app file, load preset airport and let it download.

## Authors

- [@kubatywonek](https://www.github.com/kubatywonek)
- [@pawellitwinski112](https://www.github.com/pawellitwinski112)

