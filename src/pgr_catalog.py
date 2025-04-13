import base64
import struct

class ByteReader:
    def __init__(self, data: bytes):
        self.data = data
        self.position = 0

    def read(self, length: int):
        self.position += length
        return self.data[self.position - length : self.position]
    
    def readInt(self):
        return struct.unpack("<i", self.read(4))[0]

class ByteWriter:
    def __init__(self):
        self.data = bytearray()
    
    def write(self, data: bytes):
        self.data.extend(data)
    
    def writeInt(self, value: int):
        self.write(struct.pack("<i", value))

def decrypt(catalog: dict):
    key = base64.b64decode(catalog["m_KeyDataString"])
    bucket = base64.b64decode(catalog["m_BucketDataString"])
    entry = base64.b64decode(catalog["m_EntryDataString"])
    
    table = []
    reader = ByteReader(bucket)
    
    for _ in range(reader.readInt()):
        key_position = reader.readInt()
        key_type = key[key_position]
        key_position += 1
        
        match key_type:
            case 0 | 1:
                length = key[key_position]
                key_position += 4
                key_value = key[key_position:key_position + length].decode("utf-8" if key_type == 0 else "utf-16")
                
            case 4:
                key_value = key[key_position]
        
        for _ in range(reader.readInt()):
            entry_position = reader.readInt()
            entry_value = int.from_bytes(entry[4 + 28 * entry_position : 4 + 28 * entry_position + 28][8:10], "little")
            
        table.append([key_value, entry_value])
        
    for i in range(len(table)):
        if table[i][1] != 65535:
            table[i][1] = table[table[i][1]][0]

    return table

# by deepseek
def encrypt(ori: dict, table: list):
    key_writer = ByteWriter()
    key_positions = []
    
    for key_value, _ in table:
        start_pos = len(key_writer.data)
        key_positions.append(start_pos)
        
        if isinstance(key_value, str):
            encoded = key_value.encode("utf-8")
            length = len(encoded)
            key_writer.write(bytes([0]))
            key_writer.writeInt(length)
            key_writer.write(encoded)
        elif isinstance(key_value, int) and 0 <= key_value <= 255:
            key_writer.write(bytes([4]))
            key_writer.write(bytes([key_value]))
        else:
            raise ValueError(f"Unsupported key value type: {type(key_value)}")
    
    bucket_writer = ByteWriter()
    bucket_writer.writeInt(len(table))
    
    for idx in range(len(table)):
        key_pos = key_positions[idx]
        bucket_writer.writeInt(key_pos)
        bucket_writer.writeInt(1)
        bucket_writer.writeInt(idx)
    
    entry_writer = ByteWriter()
    entry_writer.writeInt(len(table))
    
    key_map = {key: idx for idx, (key, _) in enumerate(table)}
    
    for _, entry_value in table:
        if entry_value == 65535:
            value = 65535
        else:
            value = key_map.get(entry_value, 65535)
        
        entry_bytes = bytearray(28)
        entry_bytes[8:10] = struct.pack("<H", value)
        entry_writer.write(entry_bytes)
    
    result = ori.copy()
    result["m_KeyDataString"] = base64.b64encode(key_writer.data).decode("utf-8")
    result["m_BucketDataString"] = base64.b64encode(bucket_writer.data).decode("utf-8")
    result["m_EntryDataString"] = base64.b64encode(entry_writer.data).decode("utf-8")
    
    return result
