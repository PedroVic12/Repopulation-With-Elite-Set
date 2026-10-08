-- Regras de Domínio e Hash para VbtSportMetrics
local Rules = {}
Rules.__index = Rules

function Rules:new()
    return setmetatable({ screen = "VbtSportMetrics" }, Rules)
end

function Rules:process_event(param)
    local raw = string.format("%s_%s_%d", self.screen, param, os.time())
    print("[Lua Rule Engine] Evento processado para: " .. raw)
    return raw
end

return Rules
