from hdx.location.country import Country

Country.set_use_live_default(False)

Country.countriesdata(
    country_name_overrides={"PSE": "oPt"},
    country_name_mappings={"Congo DR": "COD"},
)
