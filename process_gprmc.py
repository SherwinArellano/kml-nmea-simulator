# process_gprmc.py

def extract_gprmc_lines(input_file):
    with open(input_file, 'r', encoding='utf-8') as file:
        return [line.rstrip('\n') for line in file if line.startswith('$GPRMC')]

def reverse_lines(lines):
    return list(reversed(lines))

def write_lines_to_file(lines, output_file):
    with open(output_file, 'w', encoding='utf-8') as file:
        for line in lines:
            file.write(line + '\n')

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 3:
        print("Usage: python process_gprmc.py <input_file> <output_file>")
    else:
        input_file = sys.argv[1]
        output_file = sys.argv[2]

        gprmc_lines = extract_gprmc_lines(input_file)
        merged_lines = gprmc_lines + reverse_lines(gprmc_lines)[1:]
        write_lines_to_file(merged_lines, output_file)
