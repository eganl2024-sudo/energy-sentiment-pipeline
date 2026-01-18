# src/config.py

# Tickers
TICKERS = {
    'Crude_Oil': 'CL=F',
    'Gasoline': 'RB=F',
    'Heating_Oil': 'HO=F',
    'Natural_Gas': 'NG=F',  # <--- NEW: Energy Cost Input
    'Valero': 'VLO',
    'Phillips66': 'PSX'
}

# Valero (VLO) Assumptions
VLO_DEFAULTS = {
    'throughput_bpd': 2_900_000,
    'capture_rate': 0.85,
    'current_ebitda': 14_000_000_000,
    'ev_ebitda_multiple': 6.5,
    'shares_outstanding': 340_000_000
}

# OpEx Assumptions (Phase 7)
OPEX_DEFAULTS = {
    'nat_gas_intensity': 0.45, # MMBtu of NatGas per Barrel of Crude processed
    'fixed_opex': 6.00         # Fixed OpEx (Labor, Maintenance, catalysts) in $/bbl
}

MARKET_EVENTS = [
    ('2020-03-01', 'COVID Crash'),
    ('2022-02-24', 'Russia-Ukraine War'),
    ('2022-06-01', 'Peak Refining Margins')
]
