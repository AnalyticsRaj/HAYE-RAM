import asyncio
import os
from dotenv import load_dotenv
from telethon import TelegramClient, events
from pytgcalls import PyTgCalls, idle
from pytgcalls.types import Update
from pytgcalls.types.input_stream import InputAudioStream

# ---------- LOAD ENV ----------
load_dotenv()
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
PHONE = os.getenv('PHONE')
CHANNEL_ID = int(os.getenv('CHANNEL_ID'))   # e.g., -1001234567890
AUDIO_FILE = os.getenv('AUDIO_FILE', 'voice.ogg')
# ------------------------------

# Initialize Telethon client (userbot)
client = TelegramClient('vc_session', API_ID, API_HASH)

# Initialize PyTgCalls with the same client
app = PyTgCalls(client)

# Global state
vc_active = False
playing = False

# ---------- COMMAND HANDLERS (outgoing messages only) ----------
@client.on(events.NewMessage(pattern='/startvc', outgoing=True))
async def start_vc(event):
    global vc_active, playing
    if vc_active:
        await event.edit('⚠️ VC is already active!')
        return
    
    try:
        # Get the channel entity from ID
        entity = await client.get_entity(CHANNEL_ID)
        # Start the voice chat
        await app.start()
        await app.join_group_call(
            entity,
            InputAudioStream(AUDIO_FILE),
            enable_audio=True,
        )
        vc_active = True
        playing = True
        await event.edit(f'✅ Voice Chat started in channel {CHANNEL_ID}! Playing **{AUDIO_FILE}** continuously.')
    except Exception as e:
        await event.edit(f'❌ Failed to start VC: {e}')

@client.on(events.NewMessage(pattern='/stopvc', outgoing=True))
async def stop_vc(event):
    global vc_active, playing
    if not vc_active:
        await event.edit('⚠️ No active VC to stop.')
        return
    try:
        entity = await client.get_entity(CHANNEL_ID)
        await app.leave_group_call(entity)
        vc_active = False
        playing = False
        await event.edit('🛑 Voice Chat stopped.')
    except Exception as e:
        await event.edit(f'❌ Error stopping VC: {e}')

@client.on(events.NewMessage(pattern='/pause', outgoing=True))
async def pause_audio(event):
    global playing
    if not vc_active:
        await event.edit('⚠️ VC not active.')
        return
    if not playing:
        await event.edit('⚠️ Already paused.')
        return
    try:
        entity = await client.get_entity(CHANNEL_ID)
        await app.pause_stream(entity)
        playing = False
        await event.edit('⏸️ Playback paused.')
    except Exception as e:
        await event.edit(f'❌ Error: {e}')

@client.on(events.NewMessage(pattern='/resume', outgoing=True))
async def resume_audio(event):
    global playing
    if not vc_active:
        await event.edit('⚠️ VC not active.')
        return
    if playing:
        await event.edit('⚠️ Already playing.')
        return
    try:
        entity = await client.get_entity(CHANNEL_ID)
        await app.resume_stream(entity)
        playing = True
        await event.edit('▶️ Playback resumed.')
    except Exception as e:
        await event.edit(f'❌ Error: {e}')

@client.on(events.NewMessage(pattern='/help', outgoing=True))
async def help_cmd(event):
    help_text = (
        "**🎧 VC Bot Commands**\n"
        "/startvc – Start VC and play audio\n"
        "/stopvc  – Stop VC\n"
        "/pause   – Pause playback\n"
        "/resume  – Resume playback\n"
        "/help    – Show this message"
    )
    await event.edit(help_text)

# ---------- AUTO-RESTART WHEN AUDIO ENDS (continuous loop) ----------
@app.on_stream_end()
async def on_stream_end(update: Update):
    global playing, vc_active
    if not vc_active:
        return
    # If stream ended and VC is still active, restart playback
    if playing:
        chat_id = update.chat_id
        try:
            await app.change_stream(
                chat_id,
                InputAudioStream(AUDIO_FILE),
            )
        except Exception as e:
            print(f"Restart error: {e}")

# ---------- START THE USERBOT ----------
async def main():
    await client.start(phone=PHONE)
    print('🚀 Userbot started! Send commands in any chat (e.g., Saved Messages):')
    print('/startvc  - start VC and play audio')
    print('/stopvc   - stop VC')
    print('/pause    - pause playback')
    print('/resume   - resume playback')
    print('/help     - show help')
    await idle()

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print('Exiting...')
