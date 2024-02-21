import argparse
import gzip
import shutil
import subprocess
import pycmap
import pandas as pd


# Function to parse command-line arguments
def parse_arguments():
    parser = argparse.ArgumentParser(description="Process input and output paths.")
    parser.add_argument("--input", type=str, help="Path to the input dataset CSV file.")
    parser.add_argument(
        "--output", type=str, help="Path to save the colocalized dataset CSV file."
    )
    parser.add_argument(
        "--cmap_api_key",
        type=str,
        help="""
        Your specific CMAP API key. This can be obtained at https://simonscmap.com/apikeymanagement
        """,
    )
    return parser.parse_args()


# Parse command-line arguments
args = parse_arguments()

# Set the CMAP API key
pycmap.API(token=args.cmap_api_key)

# Define targets, which tables and variables and at what tolerances
targets = {
    "tblAltimetry_REP_Signal": {
        "variables": ["sla"],
        "tolerances": [
            1,
            0.25,
            0.25,
            1,
        ],
    },
    "tblAltimetry_NRT_Signal": {
        "variables": ["sla"],
        "tolerances": [
            1,
            0.25,
            0.25,
            1,
        ],
    },
    "tblCHL_REP": {"variables": ["chl"], "tolerances": [4, 0.25, 0.25, 1]},
    "tblModis_AOD_REP": {
        "variables": ["AOD"],
        "tolerances": [
            15,
            0.5,
            0.5,
            1,
        ],  # Sources of these particles include: volcanic ash, wildfire smoke, windblown sand and dust
    },
    "tblModis_PAR": {"variables": ["PAR"], "tolerances": [15, 0.5, 0.5, 1]},
    "tblSSS_NRT": {"variables": ["sss"], "tolerances": [1, 0.25, 0.25, 1]},
    "tblSST_AVHRR_OI_NRT": {"variables": ["sst"], "tolerances": [1, 0.25, 0.25, 1]},
    "tblWind_NRT_hourly": {
        "variables": [
            # wind_speed", # no longer available
            # "wind_curl", # FIXME: Exists in CMAP docs of Feb 2021 but causes KeyError crash
            "stress_curl",
        ],
        "tolerances": [1, 0.25, 0.25, 1],
    },
    "tblDarwin_Nutrient": {
        "variables": ["DIN", "PO4", "FeT", "O2", "SiO2"],
        "tolerances": [2, 0.5, 0.5, 5],
    },
    "tblDarwin_Ecosystem": {
        "variables": [
            "phytoplankton_diversity_shannon_index",
            "phytoplankton",
            "zooplankton",
            "CHL",
            "primary_production",
        ],
        "tolerances": [2, 0.5, 0.5, 5],
    },
    "tblDarwin_Phytoplankton": {
        "variables": [
            "diatom",
            "coccolithophore",
            "mixotrophic_dinoflagellate",
            "picoeukaryote",
            "picoprokaryote",
        ],
        "tolerances": [2, 0.5, 0.5, 5],
    },
    "tblDarwin_Nutrient_Climatology": {
        "variables": [
            "DIC_darwin_clim",
            "NH4_darwin_clim",
            "NO2_darwin_clim",
            "NO3_darwin_clim",
            "PO4_darwin_clim",
            "SiO2_darwin_clim",
            "FeT_darwin_clim",
            "DOC_darwin_clim",
            "DON_darwin_clim",
            "DOP_darwin_clim",
            "DOFe_darwin_clim",
            "POC_darwin_clim",
            "PON_darwin_clim",
            "POSi_darwin_clim",
            "POFe_darwin_clim",
            "PIC_darwin_clim",
            "ALK_darwin_clim",
            "O2_darwin_clim",
            "CDOM_darwin_clim",
        ],
        "tolerances": [2, 0.5, 0.5, 5],
    },
    "tblPisces_NRT": {
        "variables": ["NO3", "PO4", "Fe", "O2", "Si", "PP", "PHYC", "CHL"],
        "tolerances": [4, 0.5, 0.5, 5],
    },
    # 	"tblArgoMerge_REP": {
    #                                  "variables": ["argo_merge_salinity_adj", "argo_merge_temperature_adj", "argo_merge_O2_adj", "argo_merge_turbidity_adj", "argo_merge_chl_adj", "argo_merge_cdom_adj", "argo_merge_NO3", "argo_merge_NO3_adj",
    # 		"argo_merge_ph_adj"],
    #                                  "tolerances": [1, 1, 1, 5]
    #                                  },
    "tblArgo_MLD_Climatology": {
        "variables": [
            "mls_da_argo_clim",
            "mls_dt_argo_clim",
            "mlt_da_argo_clim",
            "mlt_dt_argo_clim",
            "mlpd_da_argo_clim",
            "mlpd_dt_argo_clim",
            "mld_da_mean_argo_clim",
            "mld_dt_mean_argo_clim",
            "mld_da_median_argo_clim",
            "mld_dt_median_argo_clim",
        ],
        "tolerances": [1, 1, 1, 5],
    },
    "tblGlobalDrifterProgram": {"variables": ["sst"], "tolerances": [1, 0.25, 0.25, 1]},
    # 	"tblMercator_MLD_NRT": {
    #                                  "variables": ["mld_nrt"],
    #                                  "tolerances": [1, 1, 1, 5]
    #                                  },
    "tblWOA_2018_MLD_qrtdeg_Climatology": {
        "variables": ["M_an_clim", "M_mn_clim"],
        "tolerances": [1, 0.5, 0.5, 5],
    },
    "tblWOA_2018_MLD_1deg_Climatology": {
        "variables": ["M_an_clim", "M_mn_clim"],
        "tolerances": [1, 0.5, 0.5, 5],
    },
    "tblWOA_2018_qrtdeg_Climatology": {
        "variables": [
            "C_an_clim",
            "C_mn_clim",
            "s_an_clim",
            "s_mn_clim",
            "t_an_clim",
            "t_mn_clim",
            "I_an_clim",
            "I_mn_clim",
        ],
        "tolerances": [1, 0.5, 0.5, 5],
    },
    "tblWOA_2018_1deg_Climatology": {
        "variables": [
            "C_an_clim",
            "C_mn_clim",
            "s_an_clim",
            "s_mn_clim",
            "t_an_clim",
            "t_mn_clim",
            "A_an_clim",
            "A_mn_clim",
            "O_an_clim",
            "O_mn_clim",
            "I_an_clim",
            "I_mn_clim",
            "n_an_clim",
            "n_mn_clim",
            "p_an_clim",
            "p_mn_clim",
            "si_an_clim",
            "si_mn_clim",
        ],
        "tolerances": [1, 1, 1, 5],
    },
    "tblWOA_Climatology": {
        "variables": [
            "sea_water_temp_WOA_clim",
            "density_WOA_clim",
            "salinity_WOA_clim",
            "nitrate_WOA_clim",
            "phosphate_WOA_clim",
            "silicate_WOA_clim",
            "oxygen_WOA_clim",
            "AOU_WOA_clim",
            "o2sat_WOA_clim",
            "conductivity_WOA_clim",
        ],
        "tolerances": [1, 1, 1, 5],
    },
}

# Print Pycmap version
print(f"pycmap version: {pycmap.__version__}")

# Load data from the specified input path
data: pd.DataFrame = pd.read_csv(filepath_or_buffer=args.input, sep="\t", comment='#')

# Colocalize the data
print(
    f"""
This should take awhile depending of the size of your dataframe and number of cores. 
Colocalizing data with CMAP.
    """
)

# Colocalize data
cDF: pd.DataFrame = pycmap.Sample(
    source=data, targets=targets, replaceWithMonthlyClimatolog=True
)

# specify temporary csv file
temp_csv_path = "temp_colocalized_df.csv"

# Save the colocalized dataset as a CSV file
cDF.to_csv(path_or_buf=temp_csv_path, index=False)

# Compress the temp CSV file with gzip
with open(file=temp_csv_path, mode="rb") as f_in, gzip.open(
    args.output, mode="wb"
) as f_out:
    shutil.copyfileobj(fsrc=f_in, fdst=f_out)

print(
    f"""
Colocalized dataset saved and compressed to {args.output}
    """
)

subprocess.run(args=["rm", temp_csv_path])

print(
    f"""
Remove temporary CSV file
    """
)
# # Save the colocalized dataset to the specified output path
# cDF.to_csv(args.output, index=False)
