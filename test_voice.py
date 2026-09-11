import asyncio, tempfile, os, ctypes, edge_tts

async def test():
    c = edge_tts.Communicate('Hello sir, Jarvis neural voice is online and ready.', 'en-GB-RyanNeural')
    with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as f:
        path = f.name
    await c.save(path)
    winmm = ctypes.windll.winmm
    safe = path.replace('/', '\\')
    winmm.mciSendStringW(f'open "{safe}" type mpegvideo alias test', None, 0, 0)
    winmm.mciSendStringW('play test wait', None, 0, 0)
    winmm.mciSendStringW('close test', None, 0, 0)
    os.unlink(path)
    print('Edge TTS voice test complete!')

asyncio.run(test())
