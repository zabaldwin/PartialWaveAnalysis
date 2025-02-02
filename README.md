# PartialWaveAnalysis

Usage: This repo contains all the code I use to perform a partial wave analysis using the AmpTools software provided by IU at GlueX. To utilize this software, you must already have access to the [halld_sim](https://github.com/JeffersonLab/halld_sim) suite of programs, since this code calls upon `FitResults.h` and `fit.C` from the AmpTools library and `split_mass`. ~~You also need access to the [gluex_root_analysis](https://github.com/JeffersonLab/gluex_root_analysis) program [`tree_to_amptools`](https://github.com/JeffersonLab/gluex_root_analysis/tree/master/programs/tree_to_amptools).~~ I no longer advocate the use of `tree_to_amptools` since it seems to not always create the right number of final state particles when running over generated thrown trees.

1. Create flat trees from MC Thrown, MC Reconstructed, Data, and (optional) Background ROOT TTrees.
    1. Use [`SetupAmpTools_FlatTree()`](https://github.com/JeffersonLab/gluex_root_analysis/blob/a2c0dddc6e7b3fce28bb1919843ca676c4482975/libraries/DSelector/DSelector.cc#L932) and [`FillAmpTools_FlatTree`](https://github.com/JeffersonLab/gluex_root_analysis/blob/a2c0dddc6e7b3fce28bb1919843ca676c4482975/libraries/DSelector/DSelector.cc#L948) in a DSelector (make sure you also tell the DSelector to fill these trees). Asside from running `SetupAmpTools_FlatTree()`, I also had to do a bit of code to get the proper trees filled:
    ```
    vector<TLorentzVector> locFinalStateP4;
    locFinalStateP4.push_back(locProtonP4);
    locFinalStateP4.push_back(locDecayingKShort1P4);
    locFinalStateP4.push_back(locDecayingKShort2P4);
    dFlatTreeInterface->Fill_Fundamental<Float_t>("Weight", 1.0); // haven't dealt with accidentals yet
    Fill_FlatTree();
    ```
    I insert this right at the end of the combo loop. A bit more work is needed to create these kinematic variables in the first place for the Thrown Trees, but the idea is exactly the same. Note that when this is run, you should avoid generating the default flat trees by running `tree_name->Process("DSelector_name.C+", "DefaultFlatOff")` in `ROOT`. Additionally, I use `hadd_rcdb.py` to divide my files by polarization and generate MC with polarized flux files (no actual polarization dependent physics is included in the MC).
2. Run `generate_config.py` to select which waves you want to include in your config file. The interface should be fairly straightforward. If you want to make yours manually, there are a few tags (preceeded by an `@` symbol) which you can find by looking in the code for `divide_data_pol.py` or `run_amptools.py` scripts.
3. Run `divide_data_pol.py` provided by this repo. Running it without arguments will show a help string with the required arguments and a short description of their usage. This program essentially wraps the `split_mass` program across the AmpTools trees you just generated.
4. Run `run_amptools.py` to actually perform the fits with `fit.C`. Again, running without arguments will display the help message.
    1. The `-p <integer>` option will allow you to specify how many multiprocessing processes to generate. This is limited by the number of cores you have available. Python unfortunately does not support multithreading due to the Python Interpreter Lock, but generally my fits haven't taken very long (31 bins with 20 iterations took about 7 minutes the last time I ran it). Don't worry about not knowing how many cores you have, this option is more to limit the number used if you do know it, otherwise, just don't use this flag and the program will generate up to 60 processes.
    2. Additionally, the `-s <integer>` option allows you to set the seed (default is `seed = 1`). The seed is used to randomly generate starting parameter values to be used for the fit. In theory, if you use the same seed and the same number of bins and iterations, all of those generated values should be consistent across each run, as long as you aren't adding new parameters to your fits.
    4. `run_amptools.py` will also call `get_fit_results`. However, if you just downloaded this repo, you need to build `get_fit_results` by going into that directory and running the command `make`. You might (probably will) get some errors about directories not existing. After creating the directories as suggested, the compilation worked. There is probably a better way to do this, but I just copied the Makefile from Naomi Jarvis, and I don't actually know how it works.
    5. You can also use the `--slurm` option to submit the fits as SLURM jobs (recommended if you are on the CMU cluster).
    6. The `gather.py` program included just re-gathers the fit data after a fit is performed. It is identical to the code run at the end of `run_amptools.py`, but exists just in case the `fit_results.txt` file gets deleted or a format changes or something.
5. If you've gotten to this step, you will now have an output directory that contains bin folders as well as a file titled `bin_info.txt` and one titled `fit_results.txt`. These are human-readable tab-separated files, so feel free to look inside them and see how they are structured. I wrote a quick script called `plot_results.py` to do some preliminary graphing, but it is very much a work-in-progress.

### TODO:
1. ~~Need to implement polarization in this analysis~~
2. ~~Need a better way of sending the proper waves in pairs to `get_fit_results` than just hoping the user writes them in a nice order~~
3. `plot_results.py` needs to be more robust and versatile. I want to be able to get separate subplots for each wave, but I want it to look nice also. I also want this program to have some command-line options to specify which waves to plot (or other things to plot)
4. `get_fit_results`
    1. ~~This program needs to be expanded to include more information about the fits, such as phases between waves and the base amplitudes from the fit.~~ Currently none of this code is suited to do any SDMEs, but eventually some separate programs should be added to handle these too.
    2. I should eventually try to implement a way to drop specific waves from the analysis. It might be easier to implement this in `run_amptools.py`.
