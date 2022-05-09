import EPMS
import pandas as pd

californication = EPMS.serialization.file("samples/Aguas De Marco.mid")
print(californication.head().to_markdown())

californication = EPMS.deserialization.file(californication)
californication.show()
