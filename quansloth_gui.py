import gradio as gr
import subprocess
import os
import time
import atexit
import PyPDF2
from openai import OpenAI

server_process = None

def cleanup():
    global server_process
    if server_process is not None:
        server_process.terminate()

atexit.register(cleanup)

def get_local_models():
    if not os.path.exists("models"):
        os.makedirs("models")
    files = [f for f in os.listdir("models") if f.endswith(".gguf")]
    return files if files else ["❌ No models found. Use custom route below."]

QUANSLOTH_ART_HTML = r"""
<div style="display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; margin-bottom: 0px;">
<pre style="font-family: 'Courier New', Courier, monospace; line-height: 1.1; color: #0ea5e9; font-weight: bold; text-shadow: 0 0 8px #0ea5e9; margin-bottom: 5px;">
   ____                         _       _   _     
  / __ \                       | |     | | | |    
 | |  | |_   _  __ _ _ __   ___| | ___ | |_| |__  
 | |  | | | | |/ _` | '_ \ / __| |/ _ \| __| '_ \ 
 | |__| | |_| | (_| | | | |\__ \ | (_) | |_| | | |
  \___\_\\__,_|\__,_|_| |_||___/_|\___/ \__|_| |_|
         [ POWERED BY TURBOQUANT+ | NVIDIA CUDA ]
</pre>
<div style='color: #94a3b8; font-size: 0.9em;'>Licensed under <b>Apache 2.0</b> | <a href='https://github.com/PacifAIst/Quansloth' target='_blank' style='color: #38bdf8; text-decoration: none;'>⭐ Star us on GitHub: PacifAIst/Quansloth</a></div>
</div>
"""

client = OpenAI(base_url="http://127.0.0.1:8080/v1", api_key="sk-no-key-required")

def launch_engine(model_source, dropdown_val, custom_route, preset, k_cache, v_cache, context_size):
    global server_process
    
    yield (
        "⏳ Forging Engine...", "📊 **Stats:** Intercepting live C++ engine logs...",
        gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False),
        gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False),
        gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False),
        gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
    )
    
    if server_process is not None:
        server_process.terminate()
        time.sleep(1)

    if model_source == "Local 'models/' Folder":
        if dropdown_val and not dropdown_val.startswith("❌"):
            absolute_model_path = os.path.join(os.getcwd(), "models", dropdown_val)
        else:
            yield (
                "❌ ERROR: Select a valid model from the folder.", "", 
                gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
                gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
                gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
                gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
            )
            return
    else:
        if custom_route and custom_route.strip() != "":
            absolute_model_path = custom_route.strip()
        else:
            yield (
                "❌ ERROR: Enter a valid absolute path.", "", 
                gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
                gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
                gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
                gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
            )
            return

    server_path = "../llama-cpp-turboquant/build/bin/llama-server"

    if "Standard Safe" in preset:
        ui_k, ui_v = "q4_0", "q4_0"
    elif "Turbo 3" in preset:
        ui_k, ui_v = "turbo3", "turbo3"
    elif "Turbo 4" in preset:
        ui_k, ui_v = "q8_0", "turbo4"
    else:
        ui_k, ui_v = k_cache, v_cache

    cmd = [
        server_path, "-m", absolute_model_path,
        "-ctk", ui_k, "-ctv", ui_v,
        "-c", str(context_size), "-ngl", "99",
        "-fit", "off", "-fa", "1",
        "--host", "127.0.0.1", "--port", "8080"
    ]
        
    try:
        log_file = open("engine_stats.log", "w")
        server_process = subprocess.Popen(cmd, stdout=log_file, stderr=subprocess.STDOUT) 
        time.sleep(10) 
        
        if server_process.poll() is not None:
            yield (
                "❌ ENGINE CRASHED. The model architecture might be incompatible. Try the 'Standard Safe (Q4_0)' preset.", "", 
                gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
                gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
                gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
                gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
            )
            return
            
        real_kv_size = "Unknown"
        with open("engine_stats.log", "r") as f:
            for line in f:
                if "llama_kv_cache: size =" in line:
                    real_kv_size = line.split("=")[1].split("(")[0].strip()
        
        if "MiB" in real_kv_size:
            actual_mb = float(real_kv_size.replace("MiB", "").strip())
            
            if ui_v == "turbo3":
                comp_mult = 5.12
            elif ui_v in ["turbo4", "q4_0", "turbo2"]:
                comp_mult = 4.0
            elif ui_v == "q8_0":
                comp_mult = 2.0
            else:
                comp_mult = 1.0
                
            f16_mb = actual_mb * comp_mult 
            saved_mb = f16_mb - actual_mb
            compression_pct = (saved_mb / f16_mb) * 100 if f16_mb > 0 else 0

            stats_msg = f"""
            ### 📊 Live Hardware Analytics (Intercepted)
            * **Real GPU Allocation:** {actual_mb:.2f} MB
            * **Without Compression (F16):** ~{f16_mb:.2f} MB
            * **Real VRAM Saved:** {saved_mb:.2f} MB ({compression_pct:.0f}% Compression)
            """
        else:
            stats_msg = f"### 📊 Live Hardware Analytics\n* **Real GPU Allocation:** {real_kv_size}\n* Compression mode not active or unrecognized."

        model_name = os.path.basename(absolute_model_path)
        status_msg = f"🔥 SUCCESS: Engine Online! | Model: {model_name} | Mode: K={ui_k}, V={ui_v}"
        
        yield (
            status_msg, stats_msg, 
            gr.update(interactive=False), gr.update(interactive=True), gr.update(interactive=False),
            gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False),
            gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False),
            gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True)
        )
        
    except Exception as e:
        yield (
            f"❌ ERROR: {str(e)}", "", 
            gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
            gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
            gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
            gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
        )

def stop_engine():
    global server_process
    if server_process is not None:
        server_process.terminate()
        server_process = None
        return (
            "🛑 SERVER STOPPED.", "📊 **Stats:** Offline.", 
            gr.update(interactive=True), gr.update(interactive=False), gr.update(interactive=True),
            gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
            gr.update(interactive=True), gr.update(interactive=True), gr.update(interactive=True),
            gr.update(interactive=False), gr.update(interactive=False), gr.update(interactive=False)
        )
    return "⚠️ Not running.", "", gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update(), gr.update()

def extract_document_text(file_obj):
    if file_obj is None:
        return ""
    try:
        text = f"\n\n--- CONTENTS OF ATTACHED DOCUMENT ({os.path.basename(file_obj.name)}) ---\n"
        if file_obj.name.endswith('.pdf'):
            reader = PyPDF2.PdfReader(file_obj.name)
            for page in reader.pages:
                text += page.extract_text() + "\n"
        else:
            with open(file_obj.name, 'r', encoding='utf-8', errors='ignore') as f:
                text += f.read()
        return text + "\n--------------------------------------------------\n"
    except Exception as e:
        return f"\n[Error reading document: {str(e)}]\n"

def user_message(message, history_state):
    history_state.append({"role": "user", "content": message})
    history_state.append({"role": "assistant", "content": ""}) 
    return "", history_state[::-1], history_state

def bot_response(history_state, sys_prompt, temperature, max_tokens, doc_file):
    doc_context = extract_document_text(doc_file)
    final_sys_prompt = sys_prompt + doc_context
    
    messages_for_api = [{"role": "system", "content": final_sys_prompt}]
    
    for msg in history_state[:-1]:
        messages_for_api.append({"role": msg["role"], "content": msg["content"]})
    
    try:
        stream = client.chat.completions.create(
            model="local-model", messages=messages_for_api, stream=True,
            temperature=temperature, max_tokens=max_tokens
        )
        for chunk in stream:
            if chunk.choices[0].delta.content:
                history_state[-1]["content"] += chunk.choices[0].delta.content
                yield history_state[::-1], history_state
    except Exception as e:
        history_state[-1]["content"] = f"❌ API Error: {str(e)}. Make sure the engine is running!"
        yield history_state[::-1], history_state

quansloth_theme = gr.themes.Monochrome(
    primary_hue="cyan", secondary_hue="blue", neutral_hue="slate",
    font=[gr.themes.GoogleFont("Inter"), "ui-sans-serif", "system-ui", "sans-serif"]
).set(
    body_background_fill="#0b0f19", block_background_fill="#111827",
    block_border_width="1px", block_border_color="#1e293b",
    block_title_text_color="#38bdf8", button_primary_background_fill="#0ea5e9",
    button_primary_background_fill_hover="#38bdf8", button_primary_text_color="#ffffff",
    panel_background_fill="#0f172a", input_background_fill="#1e293b",
)

with gr.Blocks() as demo:
    gr.HTML(QUANSLOTH_ART_HTML)
    
    chat_state = gr.State([])
    
    with gr.Row():
        with gr.Column(scale=1):
            with gr.Group():
                gr.Markdown("### ⚙️ 1. Start The Engine")
                
                model_source_radio = gr.Radio(
                    choices=["Local 'models/' Folder", "Custom Absolute Path"], 
                    label="Model Source", value="Local 'models/' Folder"
                )
                
                model_dropdown = gr.Dropdown(
                    choices=get_local_models(), 
                    label="Select File", 
                    value=get_local_models()[0],
                    info="Auto-scanned from your local directory."
                )
                custom_route = gr.Textbox(
                    label="Custom Absolute Path", 
                    placeholder="/home/user/downloads/model.gguf",
                    visible=False
                )
                
                preset_select = gr.Radio(
                    choices=["Symmetric (TurboQuant+ Turbo 3)", "Asymmetric (Q8 / TurboQuant+ Turbo 4)", "Standard Safe (Q4_0)", "Custom"], 
                    label="Compression Presets", value="Standard Safe (Q4_0)",
                    info="⚠️ Use 'Standard Safe' for tiny 1B models. Use Asymmetric for Qwen models."
                )
                
                with gr.Group(visible=False) as adv_group:
                    gr.Markdown("_The Key (K) and Value (V) cache store the AI's memory. Compressing V saves the most VRAM._")
                    with gr.Row():
                        k_select = gr.Dropdown(["turbo3", "turbo4", "turbo2", "q8_0", "q4_0", "f16"], label="Key Cache (K)", value="turbo3")
                        v_select = gr.Dropdown(["turbo3", "turbo4", "turbo2", "q8_0", "q4_0", "f16"], label="Value Cache (V)", value="turbo3")
                
                ctx_slider = gr.Slider(
                    minimum=2048, maximum=1000000, step=2048, value=8192, 
                    label="Context Size (Tokens)",
                    info="Higher values allow longer memory but use more VRAM."
                )
                
                with gr.Row():
                    launch_btn = gr.Button("🚀 LAUNCH", variant="primary")
                    stop_btn = gr.Button("🛑 STOP", variant="stop", interactive=False)
                    
                console_log = gr.Textbox(label="Status", lines=1, interactive=False)
                stats_log = gr.Markdown("📊 **Hardware Stats:** Waiting for engine...")
                
            with gr.Accordion("🧠 2. AI Settings & Personality", open=False):
                sys_prompt = gr.Textbox(
                    label="System Prompt", lines=2, 
                    value="You are a highly intelligent local AI. Answer in a helpful, concise manner.",
                    info="Defines the AI's core personality and rules."
                )
                temp_slider = gr.Slider(
                    minimum=0.0, maximum=2.0, step=0.1, value=0.7, 
                    label="Temperature (Creativity)",
                    info="0.0 is strict/logical, 2.0 is highly creative/chaotic."
                )
                max_tokens = gr.Slider(
                    minimum=100, maximum=1000000, step=100, value=1024, 
                    label="Max Output Tokens",
                    info="Limits how long the AI's response can be."
                )
                
        with gr.Column(scale=2):
            with gr.Group():
                gr.Markdown("### 💬 3. Talk to the Model")
                
                chatbot = gr.Chatbot(
                    label="Quansloth Interface", 
                    height=650
                )
                
                with gr.Row(equal_height=True):
                    msg_input = gr.Textbox(placeholder="Type your message and press Enter or click Send...", container=False, scale=5, interactive=False)
                    send_btn = gr.Button("📤 Send", variant="primary", scale=1, interactive=False)
                
                gr.Markdown("#### 📄 Context Injector (Test TurboQuant's Memory)")
                doc_upload = gr.File(label="Upload Context (PDF, TXT, MD, CSV, etc.)", interactive=False)
            
    model_source_radio.change(
        fn=lambda s: (gr.update(visible=(s=="Local 'models/' Folder")), gr.update(visible=(s=="Custom Absolute Path"))),
        inputs=[model_source_radio],
        outputs=[model_dropdown, custom_route],
        show_progress="hidden"
    )

    preset_select.change(
        fn=lambda p: gr.update(visible=(p == "Custom")),
        inputs=[preset_select],
        outputs=[adv_group],
        show_progress="hidden"
    )

    # OUTPUT_LIST updated to perfectly match 14 items (removed export_btn)
    OUTPUT_LIST = [console_log, stats_log, launch_btn, stop_btn, model_source_radio, model_dropdown, custom_route, preset_select, ctx_slider, k_select, v_select, msg_input, send_btn, doc_upload]

    launch_btn.click(
        launch_engine, 
        [model_source_radio, model_dropdown, custom_route, preset_select, k_select, v_select, ctx_slider], 
        OUTPUT_LIST
    )
    
    stop_btn.click(
        stop_engine, 
        outputs=OUTPUT_LIST
    )
    
    msg_input.submit(user_message, [msg_input, chat_state], [msg_input, chatbot, chat_state]).then(
        bot_response, [chat_state, sys_prompt, temp_slider, max_tokens, doc_upload], [chatbot, chat_state]
    )
    send_btn.click(user_message, [msg_input, chat_state], [msg_input, chatbot, chat_state]).then(
        bot_response, [chat_state, sys_prompt, temp_slider, max_tokens, doc_upload], [chatbot, chat_state]
    )

if __name__ == "__main__":
    demo.launch(server_name="0.0.0.0", server_port=7860, theme=quansloth_theme)