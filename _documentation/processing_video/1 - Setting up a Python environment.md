# 1 - Setting up a Python environment

For processing and analysing footage produced by the LEC instrument, we recommend setting up a Python environment on your own PC. The Python environment we use and recommend is [MiniConda](https://docs.conda.io/projects/miniconda/en/latest/). To set up MiniConda please follow these steps:

### Install Python if you don't have it

For installers for Windows, MacOs and Linux, please head over to the following website: https://www.python.org/downloads/. These installers will walk you through the installation process for your system. 

### Install MiniConda

To download and install MiniConda, head over to the following documentation: https://docs.conda.io/projects/miniconda/en/latest/. There will be both installers which will walk you through the installation process, but also command line instructions at the bottom of the page if you prefer installing via the terminal.

### Setting up a MiniConda environment

Once the installation step above has completed, open a terminal window and run the following commands:

**Create the Conda environment**
```bash
conda create -n lec python=3.9
```

**To enter the environment**
```bash
conda activate lec
```

**To exit the environment**
```bash
conda deactivate lec
```

Now we need to install the Python dependencies for processing the footage:

```bash
# Enter the lec environment
conda activate lec

# Install the dependencies
pip3 install -r requirements.txt
```

Once this process has completed you will now have a set up the environment ready to process video from the LEC instrument!