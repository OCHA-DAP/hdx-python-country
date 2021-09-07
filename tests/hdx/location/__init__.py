from hdx.location.country import Country

Country.countriesdata(
    use_live=False,
    country_name_overrides={"PSE": "oPt"},
    country_name_mappings={"Congo DR": "COD"},
)
