#!/usr/bin/env python3

"""
Search for entries.

Usage:
    genomehubs search [--assembly STRING...] [--feature STRING...]
                      [--meta STRING...] [--overlap STRING...]
                      [--return STRING...] [--taxon STRING...]
                      [--gene-tree-node STRING...]
                      [--species-tree-node STRING...]
                      [--configfile YAML...] [--taxonomy-root INT]
                      [--es-host HOSTNAME] [--es-port PORT]

Options:
    --assembly STRING           Assembly name or accession.
    --feature STRING            Feature value to search.
    --meta STRING               Metadata value to search.
    --overlap STRING            Feature to overlap.
    --return STRING             Formats to return
    --taxon STRING              Taxon or clade name or taxid.
    --gene-tree-node STRING     Gene tree node name or ID.
    --species-tree-node STRING  Tree name or ID.
    --configfile YAML           YAML configuration file.
    --taxonomy-root INT         Root taxid for taxonomy index.
    --es-host HOSTNAME          Elasticseach hostname/URL.
    --es-port PORT              Elasticseach port number.

Examples:
    # 1. All data for a clade
        ./genomehubs search \
            --taxon Nymphalidae \
            --target RAW

    # 2. All butterfly genomes above contig N50 1M
        ./genomehubs search \
            --taxon Lepidoptera \
            --meta 'assembly.contig_n50>1M' \
            --return FASTA,GFF3

    # 3. All genes with a given interpro domain
        ./genomehubs search \
            --assembly Hmel2.5 \
            --feature interpro_accession=IPR123456 \
            --overlap gene \
            --return GFF3

    # 4. All genes in a clade which are single copy busco genes"
        ./genomehubs search \
            --taxon Lepidoptera \
            --feature busco_status=Complete|Fragmented \
            --overlap gene \
            --return protein.FASTA
"""

from docopt import docopt

import assembly
# import busco
# import fasta
import gff3
import gh_logger
import tree
# import interproscan
from config import config
from es_functions import test_connection

LOGGER = gh_logger.logger()
PARAMS = [{'flag': '--gff3', 'module': gff3}]


def generate_index_patterns(options):
    """Generate Elasticsearch index pattern."""
    if 'type' in options['search']:
        patterns = []
        for index_type in options['search']['type']:
            patterns.append("%s-*" % index_type)
        return patterns
    return ['*']


def generate_assembly_list(options, es):
    """Generate list of assemblies to search."""
    index = assembly.template('name', options['search'])
    meta = []
    if 'meta' in options['search'] and options['search']['meta']:
        meta = options['search']['meta']
    assemblies = []
    if 'assembly' in options['search'] and options['search']['assembly']:
        assemblies = assembly.assemblies_from_assembly(options['search']['assembly'],
                                                       meta,
                                                       es,
                                                       index)
    if 'taxon' in options['search'] and options['search']['taxon']:
        assemblies += assembly.assemblies_from_taxon(options['search']['taxon'],
                                                     meta,
                                                     es,
                                                     index)
    if 'species-tree-node' in options['search'] and options['search']['species-tree-node']:
        options['analysis-type'] = 'species_tree'
        assemblies += tree.assemblies_from_tree(options['search']['species-tree-node'],
                                                meta,
                                                es,
                                                options)
    return assemblies


def main():
    """Entrypoint for genomehubs search."""
    args = docopt(__doc__)

    # Load configuration options
    options = config('search', **args)

    # Check Elasticsearch is running
    es = test_connection(options['search'])

    # Generate index pattern and query

    assemblies = generate_assembly_list(options, es)
    # for assembly in assemblies:
    #     print(assembly['_source']['assembly_id'])
    #     print(assembly['_source']['scientific_name'])
    #     print(assembly['_source']['statistics'][0]['n50'])
    LOGGER.info("%s assemblies matched the search criteria", len(assemblies))
    # index_patterns = generate_index_patterns(options)
    # search_query = build_search_query(options)
    # if search_query:
    #     if 'suffix' in search_query and search_query['suffix']:
    #         index_patterns = ["%s%s" % (pattern, search_query['suffix']) for pattern in index_patterns]
    #         print(','.join(index_patterns))
    #     res = es.search(index=','.join(index_patterns), body=search_query)
    #     print(res)
    # else:
    #     logger.info('No query to execute')

    # # Loop through file types
    # for type in TYPES:
    #     if args[type['flag']]:
    #         # Load index template
    #         template = type['module'].template()
    #         load_template(es, template)
    #         # Generate index name
    #         index_name = generate_index_name(type, template, options)
    #         gh_logger.info("Setting index name to %s" % index_name)
    #         # Index file
    #         index_entries(es, index_name, type['module'], args[type['flag']])


if __name__ == '__main__':
    main()
