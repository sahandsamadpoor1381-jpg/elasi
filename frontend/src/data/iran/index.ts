import provincesData from "./provinces.json";
import citiesData from "./cities.json";


export type IranProvince = {
  id: number;
  name: string;
  slug: string;
  tel_prefix: string;
};


export type IranCity = {
  id: number;
  name: string;
  slug: string;
  province_id: number;
  county_id: number;
  district_id: number;
};


const persianCollator =
  new Intl.Collator(
    "fa",
    {
      sensitivity:
        "base",
    },
  );


export const iranProvinces =
  (
    provincesData as
      IranProvince[]
  )
    .slice()
    .sort(
      (
        first,
        second,
      ) =>
        persianCollator.compare(
          first.name,
          second.name,
        ),
    );


const iranCities =
  citiesData as
    IranCity[];


const provinceIdByName =
  new Map<
    string,
    number
  >(
    iranProvinces.map(
      (province) => [
        province.name,
        province.id,
      ],
    ),
  );


export function getIranCitiesByProvince(
  provinceName: string,
): IranCity[] {
  if (!provinceName) {
    return [];
  }


  const provinceId =
    provinceIdByName.get(
      provinceName,
    );


  if (
    provinceId ===
    undefined
  ) {
    return [];
  }


  return iranCities
    .filter(
      (city) =>
        city.province_id ===
        provinceId,
    )
    .slice()
    .sort(
      (
        first,
        second,
      ) =>
        persianCollator.compare(
          first.name,
          second.name,
        ),
    );
}