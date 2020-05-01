
# Strategy for extracting features

## Features

- highway length features:
    - `motorway`
    - `trunk`
    - `primary`
    - `secondary`
    - `tertiary`
    - `residential`
    - `service`
    - `footway`
    - `cycleways`
    - `other`
- highway count features:
    - `bus_stop`
    - `crossing`
    - `traffic_signals`
    - `traffic_calming`
    - `street_lamp`

## Logic

### Nodes

- Parse nodes:
    - check type:
        - `amenity`
        - `craft`
        - `highway`
            - `bus_stop`
            - `crossing`
            - `traffic_signal`
            - `traffic_calming`
        - `historic`
        - `leisure`
    - match to which hexagon they belong to and keep a reference there  

### Ways

- Parse ways and check what type it is:
    - if `highway`:
        - go node by node, create bounding box around points and check which hexagons they belong to.
            - if only 1, then measure length and add it to `highway_length` feature. 
            - if more than 1, then intersect LineString with hexagon, measure the split lines
            and add their length to the respective hexagon
        - keep track of other tags as a percentage of total length in hexagon:
            - `highway` -> check appendix below for details
            - `bicycle`
            - `cycleway`
            - `surface`
            
### Areas
         
- Parse areas:
    - if `landuse`:
        - check what type:
            - `residential`
            - `commercial`
            - `construction`
            - `industrial`
            - `retail`
            - `agricultural`
                - `allotments`
                - `farmland`
                - `farmyard`
                - `forest`
                - `meadow`
                - `orchard`
                - `vineyard`
            - `other`
        - measure area
        - intersect with hexagons and increase their area respectively
    - if `building`:
        - check type of building
    - else:
        - check if its closed (first and last nodes are equal)
        - check what type is it:
            - `amenity` -> check below fro details
            - `leisure` 
            - `craft`
            - `emergency`
            - `historic`
            
  	        
  	    
  	    
## Appendix: sub-groups:

- `amenity`
    - `sustenance`
      - `bar`
      - `bbq`
      - `biergarten`
      - `cafe`
      - `drinking_water`
      - `fast_food`
      - `food_court`
      - `ice_cream`
      - `pub`
      - `restaurant`
    - `education`
      - `college`
      - `driving_school`
      - `kindergarten`
      - `language_school`
      - `library`
      - `toy_library`
      - `music_school`
      - `school`
      - `university`
    - `transportation`
      - `bicycle_parking`
      - `bicycle_repair_station`
      - `bicycle_rental`
      - `boat_rental`
      - `boat_sharing`
      - `bus_station`
      - `car_rental`
      - `car_sharing`
      - `car_wash`
      - `vehicle_inspection`
      - `charging_station`
      - `ferry_terminal`
      - `fuel`
      - `grit_bin`
      - `motorcycle_parking`
      - `parking`
      - `parking_entrance`
      - `parking_space`
      - `taxi`
    - `Financial`
      - `atm`
      - `bank`
      - `bureau_de_change`
    - `Healthcare`
      - `baby_hatch`
      - `clinic`
      - `dentist`
      - `doctors`
      - `hospital`
      - `nursing_home`
      - `pharmacy`
      - `social_facility`
      - `veterinary`
    - `Entertainment`
      - `arts_center`
      - `brothel`
      - `casino`
      - `cinema`
      - `community_centre`
      - `fountain`
      - `gambling`
      - `nightclub`
      - `planetarium`
      - `public_bookcase`
      - `social_centre`
      - `stripclub`
      - `studio`
      - `swingerclub`
      - `theatre`
    - `Others`
      - `animal_boarding`
      - `animal_shelter`
      - `baking_oven`
      - `bench`
      - `childcare`
      - `clock`
      - `conference_centre`
      - `courthouse`
      - `crematorium`
      - `dive_centre`
      - `embassy`
      - `fire_station`
      - `give_box`
      - `grave_yard`
      - `gym` -> count as `leisure==fitness_centre`
      - `hunting_stand`
      - `internet_cafe`
      - `kitchen`
      - `kneipp_water_cure`
      - `marketplace`
      - `monastery`
      - `photo_booth`
      - `place_of_worship`
      - `police`
      - `post_box`
      - `post_depot`
      - `post_office`
      - `prison`
      - `public_bath`
      - `public_building` -> count as `office==government`
      - `ranger_station`
      - `recycling`
      - `sanitary_dump_station`
      - `sauna` -> count as `leisure==sauna`
      - `shelter`
      - `shower`
      - `telephone`
      - `toilets`
      - `townhall`
      - `vending_machine`
      - `waste_basket`
      - `waste_disposal`
      - `waste_transfer_station`
      - `watering_place`
      - `water_point` 
- `highway`
    - nodes:
        - `bus_stop`
        - `crossing`
        - `traffic_signals`
        - `traffic_calming`
        - `street_lamp`
    - ways:
        - `motorway`
            - `motorway`
            - `motorway_link`
        - `trunk`
            - `trunk`
            - `trunk_link`
        - `primary`
            - `primary`
            - `primary_link`
        - `secondary`
            - `secondary`
            - `secondary_link`
        - `tertiary`
            - `tertiary`
            - `tertiary_link`
        - `residential`
            - `residential`
            - `living_street`
        - `service`
        - `footway`
            - `footway`
            - `pedestrian`
            - `steps`
            - `bridleway`
        - `other`
        
# Future work

- Check if nodes belong to more that one building
- count waterways