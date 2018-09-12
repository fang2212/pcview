import argparse
import base64

def decode_log(log_path):
    fp = open(log_path, 'rb')
    content = fp.read()
    print(content)
    content = base64.b64decode(content)
    content = content.decode('utf-8')
    content = content.split('\n')

    for index, temp in enumerate(content):
        print(index, temp)

    fp.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--path", help="log path",
                        type=str)
    args = parser.parse_args()
    decode_log(args.path)
