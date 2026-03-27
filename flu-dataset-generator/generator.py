import json
from pathlib import Path
import sys
import zipfile
import yaml
from Bio import Entrez, SeqIO
from dataclasses import dataclass
import click

# Set your email address (required by NCBI)
Entrez.email = "your_email@example.com"

InsdcAccession = str
SequenceName = str

PATHOGEN_TEMPLATE = {
    "alignmentParams": {"minSeedCover": 0.01},
    "schemaVersion": "3.0.0",
    "attributes": {
        "name": "TODO",
        "reference name": "TODO",
        "reference accession": "TODO",
    },
    "files": {
        "reference": "reference.fasta",
        "pathogenJson": "pathogen.json",
        "genomeAnnotation": "genome_annotation.gff3",
    },
}

DATASET_TEMPLATE = {
    "path": "flu/h3n2/seg6/CY114383",
    "enabled": True,
    "attributes": {
        "name": "Influenza A/H3N2 (segment 6/NA)",
        "reference name": "Influenza A virus (A/Wisconsin/67/2005(H3N2)) segment 6, complete sequence",
        "reference accession": "CY114383.1",
    },
    "files": {
        "reference": "reference.fasta",
        "pathogenJson": "pathogen.json",
        "genomeAnnotation": "genome_annotation.gff3",
    },
    "versions": [{"tag": "unreleased"}],
    "version": {"tag": "unreleased"},
}


@dataclass
class Config:
    HA: dict[SequenceName, InsdcAccession]
    NA: dict[SequenceName, InsdcAccession]
    NS: dict[SequenceName, InsdcAccession]
    output_dir: str


def fetch_genbank_description(accession: str):
    with Entrez.efetch(
        db="nucleotide",
        id=accession,
        rettype="gb",
        retmode="text",
    ) as handle:
        return SeqIO.read(handle, "genbank").description


def update_index(pathogen_json, path, output_dir):
    index_path = Path(output_dir) / "index.json"
    index = json.loads(index_path.read_text())
    dataset = DATASET_TEMPLATE.copy()
    dataset["path"] = str(Path(path).relative_to(output_dir).parent)
    dataset["attributes"] = pathogen_json["attributes"]
    dataset["files"] = pathogen_json["files"]
    index["collections"][0]["datasets"].append(dataset)
    index_path.write_text(
        json.dumps(index, indent=2, ensure_ascii=False) + "\n"
    )

def rename_cds_to_gene_names(gff_content: str) -> str:
    lines = gff_content.splitlines()
    updated_lines = []
    for line in lines:
        if line.startswith("#") or not line.strip():
            updated_lines.append(line)
            continue
        parts = line.split("\t")
        if len(parts) < 9:
            updated_lines.append(line)
            continue
        attributes = parts[8]
        attr_dict = dict(item.split("=") for item in attributes.split(";") if "=" in item)
        if parts[2] == "CDS" and "gene" in attr_dict:
            attr_dict["Name"] = attr_dict["gene"].upper()
            del attr_dict["gene"]
            parts[8] = ";".join(f"{k}={v}" for k, v in attr_dict.items())
            updated_line = "\t".join(parts)
            updated_lines.append(updated_line)
        else:
            updated_lines.append(line)
    return "\n".join(updated_lines)


def generate_dataset(dataset_dir: Path, ref_name: str, accession: str, output_dir: str):
    dataset_dir.mkdir(parents=True, exist_ok=True)
    fasta_path = dataset_dir / "reference.fasta"
    gff_path = dataset_dir / "genome_annotation.gff3"
    pathogen_path = dataset_dir / "pathogen.json"
    zip_path = dataset_dir / "dataset.zip"

    try:
        fasta = Entrez.efetch(
            db="nucleotide", id=accession, rettype="fasta", retmode="text"
        )
        fasta_path.write_text(fasta.read())

        gff3 = Entrez.efetch(
            db="nucleotide", id=accession, rettype="gff3", retmode="text"
        )
        gff_content = gff3.read()
        gff_path.write_text(rename_cds_to_gene_names(gff_content))

        pathogen_json = PATHOGEN_TEMPLATE.copy()
        pathogen_json["attributes"]["name"] = ref_name
        pathogen_json["attributes"]["reference name"] = fetch_genbank_description(
            accession
        )
        pathogen_json["attributes"]["reference accession"] = accession

        pathogen_path.write_text(
            json.dumps(pathogen_json, indent=2, ensure_ascii=False) + "\n"
        )
        update_index(pathogen_json, dataset_dir, output_dir)
    except Exception as e:
        print(f" {dataset_dir} Failed: {e}", file=sys.stderr)

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in dataset_dir.rglob("*"):
            if path == zip_path:
                continue  # don’t zip the zip
            zf.write(path, arcname=path.relative_to(dataset_dir))


def create_datasets(config: Config) -> None:
    for ref_name, accession in config.HA.items():
        dataset_dir = Path(config.output_dir) / "flu" / "HA" / ref_name / accession / "unreleased"
        generate_dataset(dataset_dir, ref_name, accession, config.output_dir)
    for ref_name, accession in config.NA.items():
        dataset_dir = Path(config.output_dir) / "flu" / "NA" / ref_name / accession / "unreleased"
        generate_dataset(dataset_dir, ref_name, accession, config.output_dir)
    for ref_name, accession in config.NS.items():
        dataset_dir = Path(config.output_dir) / "flu" / "NS" / ref_name / accession / "unreleased"
        generate_dataset(dataset_dir, ref_name, accession, config.output_dir)


@click.command()
@click.option("--config-file", required=True, type=click.Path(exists=True))
def main(config_file: str) -> None:
    with open(config_file, encoding="utf-8") as file:
        full_config = yaml.safe_load(file)
        relevant_config = {key: full_config[key] for key in Config.__annotations__}
        config = Config(**relevant_config)
    create_datasets(config)


if __name__ == "__main__":
    main()
