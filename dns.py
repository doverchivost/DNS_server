from dnslib import DNSHeader, DNSRecord
import socket
import time
import pickle
from pprint import pprint

port = 53
localHost = "127.0.0.1"
forwarder = "8.8.4.4"
size = 1024


def writer(data):
    f = open("cache.txt", "wb")
    pickle.dump(data, f)
    f.close()


def reader():
    try:
        f = open("cache.txt", "rb")
        readCache = pickle.load(f)
        f.close()
        return readCache
    except FileNotFoundError:
        f = open("cache.txt", "x")
        return dict()
    except (OSError, EOFError) as e:
        # print("ERROR on opening cache file")
        print(e)
        return dict()


def send(c, a, p):
    header = DNSHeader(p.header.id, q=1, a=len(c.get((p.questions[0].qname, p.questions[0].qtype))[0]))
    answer = DNSRecord(header, p.questions, c.get((p.questions[0].qname, p.questions[0].qtype))[0])
    server.sendto(answer.pack(), a)


cache = reader()
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((localHost, port))


while True:
    receivedData, address = server.recvfrom(size)
    parsed = DNSRecord.parse(receivedData)

    if cache.get((parsed.questions[0].qname, parsed.questions[0].qtype)):
        print(f"Cache is used for {parsed.questions[0].qname}")
        send(cache, address, parsed)

    else:
        try:
            client.sendto(receivedData, (forwarder, port))
            DNSanswer, adr = client.recvfrom(size)
            parsedAnswer = DNSRecord.parse(DNSanswer)
            cache[(parsedAnswer.questions[0].qname, parsedAnswer.questions[0].qtype)] = parsedAnswer.rr, time.time()

            if parsedAnswer.auth:
                cache[(parsedAnswer.questions[0].qname, parsedAnswer.questions[0].qtype)] = parsedAnswer.rr, time.time()

            for allInformation in parsedAnswer.ar:
                cache[(allInformation.rname, allInformation.rtype)] = [allInformation], time.time()

            pprint(cache)
            print(f"Added to cash: {parsed.questions[0].qname}")
            writer(cache)
            send(cache, address, parsed)
        except Exception as e:
            print(e)
