| Type                                  | Value                                             | Content-Type       | Suffix          | Description                                                                  |
| ----------------------------------    | ------------------------------------------------- | ------------       | ------          | ---------------------------------------------------------------------------  |
| brain_atlas                                          | brain_atlas_annotation                                              | application/nrrd | .nrrd | Brain atlas annotation nrrd volume. |
|                                                             |                                                                                     |                             |                 
         |                                                            |
| brain_atlas                                         | brain_atlas_region_mesh                                          | application/obj  | .obj | Brain atlas region mesh geometry object. |
|                                                             |                                                                                     |                            |
       |                                                                       |
| cell\_composition                     | cell\_composition\_summary                        |                    |                 |                                                                              |
| cell\_composition                     | cell\_composition\_volumes                        |                    |                 |                                                                              |
| circuit                               | sonata\_circuit                                   | N/A                | N/A (directory) | SONATA circuit, but have a circuit\_config.json in the root of the directory |
| electrical\_cell\_recording           | nwb                                               | application/nwb            | .nwb                | Electrophysiological timeseries data                                                                             |
| emodel                                | emodel\_parametrization\_optimization\_output     |                    |                 |                                                                              |
| emodel                                | neuron\_hoc                                       |                    |                 |                                                                              |
| reconstruction\_morphology            | hdf5                                              | application/x-hdf5 | .h5             | Morphology in HDF5 format                                                    |
| reconstruction\_morphology            | neurolucida                                       | application/asc    | .asc            | Morphology in Neurolucida ASCII format                                       |
| reconstruction\_morphology            | swc                                               | application/swc    | .swc            | Morphology in SWC format                                                     |
| simulation                            | custom\_node\_sets                                |                    |                 |                                                                              |
| simulation                            | replay\_spikes                                    |                    |                 |                                                                              |
| simulation                            | simulation\_generation\_config                    |                    |                 |                                                                              |
| simulation                            | sonata\_simulation\_config                        |                    |                 |                                                                              |
| simulation\_campaign                  | campaign\_generation\_config                      |                    |                 |                                                                              |
| simulation\_campaign                  | campaign\_summary                                 |                    |                 |                                                                              |
| simulation\_result                    | spike\_report                                     |                    |                 |                                                                              |
| simulation\_result                    | voltage\_report                                   |                    |                 |                                                                              |
| single\_neuron\_simulation            | single\_neuron\_simulation\_data                    | application/json                   |.json                 | single neuron simulation configuration and timeseries output |
| single\_neuron\_synaptome             | single\_neuron\_synaptome\_config                 | application/json | .json | single neuron synaptome configuration |
| single\_neuron\_synaptome\_simulation | single\_neuron\_synaptome\_simulation\_data | application/json                   |.json                 | single neuron synaptome simulation configuration and timeseries output |
| validation\_result | validation\_result\_figure | application/pdf                   |.pdf                 | Validation result figure |
| validation\_result | validation\_result\_details | text/plain                   |.txt                 | Log and details about the validation execution |
