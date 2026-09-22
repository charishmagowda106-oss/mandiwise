"""Real Karnataka APMC markets.

`LIVE_MARKET_NAMES` are the exact market names returned by the daily AGMARKNET
sync feed, so live price records can be matched 1:1 against these rows for
distance calculations. `EXTRA_MARKETS` adds other well-known Karnataka APMCs so
farmers outside the live feed's coverage still get real nearby markets for the
profit-ranking and ML pages (their prices come from the bundled sample history,
clearly labelled as estimates).

Coordinates are town/market-town approximations, good for distance ranking.
"""

STATE = "Karnataka"

# name, district, lat, lng — names exactly as served by the live feed
LIVE_MARKET_ROWS = [
    ("APMC Hubballi", "Dharwad", 15.3647, 75.1240),
    ("APMC THIRTHAHALLI", "Shivamogga", 13.6952, 75.2405),
    ("Arasikere APMC", "Hassan", 13.3134, 76.0153),
    ("Ballari APMC", "Ballari", 15.1394, 76.9214),
    ("Bantwala APMC", "Dakshina Kannada", 12.8883, 75.0328),
    ("Belthangdi APMC", "Dakshina Kannada", 12.9305, 75.0614),
    ("Bengaluru APMC", "Bengaluru Urban", 13.0280, 77.5350),
    ("Bhadravathi APMC", "Shivamogga", 14.0242, 75.7017),
    ("Binny Mill (FF&V) Bengaluru APMC", "Bengaluru Urban", 13.0050, 77.5600),
    ("Chamarajanagar APMC", "Chamarajanagar", 11.9237, 76.9405),
    ("Channagiri APMC", "Davanagere", 14.0233, 75.9257),
    ("Chitradurga APMC", "Chitradurga", 14.2353, 76.3952),
    ("Davangere APMC", "Davanagere", 14.4644, 75.9250),
    ("Doddaballapur APMC", "Bengaluru Rural", 13.2927, 77.5371),
    ("Gundlupet APMC", "Chamarajanagar", 11.7470, 76.6216),
    ("Haliyala APMC", "Uttara Kannada", 14.3330, 74.0970),
    ("Hanagal APMC", "Uttara Kannada", 14.0200, 74.5700),
    ("HarappanaHalli APMC", "Davanagere", 14.6014, 76.6008),
    ("Hiriyur APMC", "Chitradurga", 13.9471, 76.6123),
    ("Holalkere APMC", "Chitradurga", 14.0436, 76.1869),
    ("Honnali APMC", "Davanagere", 14.2393, 75.4703),
    ("Honnavar APMC", "Uttara Kannada", 14.2752, 74.4519),
    ("Hosanagara APMC", "Shivamogga", 13.9172, 75.0614),
    ("Hoskote APMC", "Bengaluru Rural", 13.0707, 77.7980),
    ("Hunsur APMC", "Mysuru", 12.3031, 76.2966),
    ("K.R. Pet APMC", "Mandya", 12.5450, 76.8954),
    ("Kalaburagi APMC", "Kalaburagi", 17.3298, 76.8340),
    ("Koppa APMC", "Shivamogga", 15.1470, 74.9770),
    ("Kumta APMC", "Uttara Kannada", 14.3649, 74.4900),
    ("Kundapura APMC", "Udupi", 13.6305, 74.6904),
    ("Laxmeshwar APMC", "Gadag", 15.3500, 75.5710),
    ("Madikeri APMC", "Kodagu", 12.4244, 75.7382),
    ("Malur APMC", "Kolar", 13.0033, 77.8431),
    ("Mangaluru APMC", "Dakshina Kannada", 12.8747, 74.8818),
    ("Mudigere APMC", "Chikkamagaluru", 13.1407, 75.6414),
    ("Mysuru APMC", "Mysuru", 12.2958, 76.6394),
    ("Periyapatna APMC", "Mysuru", 11.9801, 76.1017),
    ("Puttur APMC", "Dakshina Kannada", 12.7604, 75.2033),
    ("Ramanagara APMC", "Ramanagara", 12.7216, 77.2833),
    ("Ranebennur APMC", "Haveri", 14.4744, 75.6344),
    ("Rona APMC", "Gadag", 15.3296, 75.7361),
    ("Sagar APMC", "Shivamogga", 14.1645, 75.0296),
    ("Shikaripura APMC", "Shivamogga", 14.2714, 75.3569),
    ("Siddapur APMC", "Uttara Kannada", 14.3796, 74.8900),
    ("Sindhanur APMC", "Raichur", 15.7700, 76.7500),
    ("Sirsi APMC", "Uttara Kannada", 14.1667, 74.8702),
    ("Sulya APMC", "Dakshina Kannada", 12.5600, 75.3500),
    ("Tarikere APMC", "Chikkamagaluru", 13.7114, 75.8167),
    ("Tumakuru APMC", "Tumakuru", 13.3392, 77.1138),
    ("Yadgir APMC", "Yadgir", 16.7700, 77.1380),
    ("Yellapur APMC", "Uttara Kannada", 14.9600, 74.5107),
    # Seen in the live price feed although absent from /v1/markets on some days
    ("Bangarpet APMC", "Kolar", 13.0227, 78.2167),
    ("Gauribidanur APMC", "Chikkaballapura", 13.6105, 77.5198),
]

# Other well-known Karnataka APMCs (not always in the live feed)
EXTRA_MARKET_ROWS = [
    ("Belagavi APMC", "Belagavi", 15.8497, 74.4977),
    ("Vijayapura APMC", "Vijayapura", 16.8302, 75.7102),
    ("Bidar APMC", "Bidar", 17.9104, 77.5196),
    ("Chikkaballapura APMC", "Chikkaballapura", 13.4328, 77.7274),
    ("Tiptur APMC", "Tumakuru", 13.7301, 76.4730),
    ("Nanjangud APMC", "Mysuru", 12.1167, 76.6837),
    ("Karwar APMC", "Uttara Kannada", 14.8097, 74.1300),
    ("Gangavathi APMC", "Koppal", 15.4308, 76.3536),
    ("Kolar APMC", "Kolar", 13.1367, 78.1283),
    ("Mandya APMC", "Mandya", 12.5217, 76.8954),
    ("Hassan APMC", "Hassan", 13.0000, 76.1000),
    ("Shivamogga APMC", "Shivamogga", 13.9299, 75.5625),
    ("Udupi APMC", "Udupi", 13.3409, 74.7493),
    ("Chikkamagaluru APMC", "Chikkamagaluru", 13.3150, 75.7750),
    ("Raichur APMC", "Raichur", 16.2044, 77.3566),
]

def _row_to_dict(row):
    name, district, lat, lng = row
    return {"name": name, "state": STATE, "district": district, "lat": lat, "lng": lng}


REAL_MANDIS = [_row_to_dict(row) for row in LIVE_MARKET_ROWS + EXTRA_MARKET_ROWS]
