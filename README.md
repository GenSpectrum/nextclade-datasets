# nextclade-datasets

This directory is a Genspectrum-maintained nextclade server, created using the docs: https://github.com/nextstrain/nextclade_data/blob/master/docs/dataset-server-maintenance.md. 

How to add new datasets?

1. Create a dataset following [nextclade's instructions](https://github.com/nextstrain/nextclade_data/blob/master/docs/dataset-creation-guide.md).
2. Update the `index.json`: this should include the details from each pathogen.json folder, additionally the `index.json` expects datasets to be versioned. For simplicity set version to unreleased and keep each dataset in a subdirectory called `unreleased`.
3. Zip the contents of the dataset into `dataset.zip` - this is what will be downloaded by nextclade and unzipped prior to use.

Note that steps 2 and 3 are performed automatically by the CI when you create an official nextclade dataset, using the [rebuild script](https://github.com/nextstrain/nextclade_data/blob/master/scripts/rebuild/). 


Download H5N1 datasets as follows:
```
for i in {1..8}; do 
    nextclade_dataset_name=flu/h5n1/seg$i
    nextclade_dataset_server=https://raw.githubusercontent.com/genspectrum/nextclade-datasets/main/data
    nextclade3 dataset get --name $nextclade_dataset_name --server $nextclade_dataset_server --output-dir output$i
done
```