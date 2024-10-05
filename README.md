# nextclade-datasets

This directory is a Genspectrum-maintained nextclade server, created using the docs: https://github.com/nextstrain/nextclade_data/blob/master/docs/dataset-server-maintenance.md. 


Download datasets as follows:
```
nextclade_dataset_name=flu/h5n1/seg1
nextclade_dataset_server=https://raw.githubusercontent.com/genspectrum/nextclade-datasets/dataset_server_test/data
nextclade3 dataset get --name $nextclade_dataset_name --server $nextclade_dataset_server --output-dir output
```