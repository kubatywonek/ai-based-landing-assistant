
# AI-based landing assistant in a simplified aircraft approach simulation

Project that utilizes NEAT algorithm to train a network that performs descent and landing on optimal flight descent path to the destination airport runway within safety envelope. Based on JSBSim flight physics engine and FlightGear for 3D visualization.




## Environment setting (non os depentent)

#### Required packages ome with Docker container

```bash
  requirements.txt / Dockerfile
```

Download Docker Desktop application on your computer and install.

Recreate the environment in Visual Studio Code through Dev Container extension from Microsoft.

    1. Clone the repository

    2. Open Visual Studio Code

    3. Install Dev Containers extension in VS Code

    4. Open the according folder on your computer

    5. Press Ctrl + Shift + P or enter '>' in the command line of VS Code

    6. Enter the command: >Dev Containers: Reopen in Container

        If the environment does not open,
        make sure you have Docker Desktop
        application running in the background

    *7. To run the filght with the 3D Visualization open fg_conf folder
        and run the script accordingly to your operating system.
        (You have to install FlightGear software manually!)

    8. Run the program by typing in the VS Code terminal: 
        cd landing_ai/src/
        python main.py



## Running 3D visualisation

If you wish to use optional 3D visualisation you need to download the os-corresponding version of [FlightGear flight simulator](https://www.flightgear.org).

FlightGear needs to be running before any Python code. To run it properly for example on linux based system use bash script in fg_conf directory:

```bash
  ./fg_conf/fg_run.sh
```

Some of preset runways may require to run FlightGear alone in that airport first in order to download maps. Simply open the FlightGear with main .app file, load preset airport and let it download.

## Authors

- [@kubatywonek](https://www.github.com/kubatywonek)
- [@pawellitwinski112](https://www.github.com/pawellitwinski112)

