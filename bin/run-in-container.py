#!/usr/bin/env python3

import argparse
import sys
from pprint import pprint

from mdcoderun import parse, execute

def main():

    argparser = argparse.ArgumentParser(
        description="Extracts code blocks from .md files and runs these code in specified container"
    )

    argparser.add_argument("files", nargs="+", metavar="nfiles", help="markdown files to be processed")
    argparser.add_argument("--container", "-c", required=True, help="Docker image id to run the code.")
    argparser.add_argument("--line-by-line", default=False, action="store_true", help="Run the commands line by line with exec, instead of running all at once.")
    argparser.add_argument("--katacoda-tag", "-k", default="", help="The Katacoda tag that will be searched in .md code blocks, e.g., for {{execute}}, specify 'execute'")
    argparser.add_argument("--no-inline", action="store_true", default = False, help="Skip `inline code elements` while parsing")
    argparser.add_argument("--no-block", action="store_true", default = False, help="Skip ```\ncode\nblocks\n``` while parsing")
    argparser.add_argument("--no-fix-initial-dollar", action="store_true", default = False, help="Don't remove initial $ signs in code blocks")
    argparser.add_argument("--no-stop", action="store_true", default = False, help="Don't stop the containers at the end.")
    argparser.add_argument("--language", "-l", default="", help="Filter the blocks by ```language\ncode\ncode\n```. Implies --no-inline, as inline code elements cannot specify language")
    argparser.add_argument("--debug", default=False, action="store_true", help="Show debug output")
    
    args = argparser.parse_args()

    container = args.container
    katacoda_tag = args.katacoda_tag
    inline = not args.no_inline
    block = not args.no_block
    stop = not args.no_stop
    line_by_line = args.line_by_line
    fix_initial_dollar = not args.no_fix_initial_dollar
    language = args.language
    debug = args.debug

    if debug:
        pprint(args)

    for md_filename in args.files:
        code_blocks = parse.parse_file(
            md_filename,
            parse_inline = inline,
            parse_blocks = block,
            katacoda_tags = [katacoda_tag],
            language = language
        )
        if line_by_line:
            for cb in code_blocks: 
                result = execute.run_in_container(container, cb.code, fix_initial_dollar=fix_initial_dollar, debug=debug)
                print(result[1])
        else:
            whole_script = "\n".join([cb.code for cb in code_blocks])
            result = execute.run_in_child_container(container, whole_script, fix_initial_dollar, debug=debug)
    if stop:
        execute.stop_containers()


if __name__ == "__main__":
    main()
