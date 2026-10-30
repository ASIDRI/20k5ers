//+------------------------------------------------------------------+
//| ExportCalendar.mq5                                                |
//| Writes the MT5 economic calendar (actual, forecast, previous,     |
//| importance, impact for the currency) to a CSV for the bot's news  |
//| score (news_strength.py).                                         |
//|                                                                   |
//| Use: MetaEditor -> open this file -> Compile. In MT5: Navigator ->|
//| Scripts -> ExportCalendar, drag onto any chart, set the inputs.   |
//| Output: <Common data folder>\Files\mt5_calendar.csv               |
//| (File -> Open Data Folder, then up one level to "Common").        |
//| Run once with a long history for the backtest, then daily (or let |
//| the bot read the file it rewrites) for live use.                  |
//+------------------------------------------------------------------+
#property script_show_inputs
#property strict

input datetime InpFrom = D'2010.01.01';   // history from
input datetime InpTo   = 0;               // until (0 = now + 7 days)
input string   InpCurrencies = "USD,EUR,GBP,JPY,CHF,CAD,AUD,NZD,CNY";
input bool     InpOnlyMedHigh = true;     // skip low-importance events
input string   InpFile = "mt5_calendar.csv";

string ImportanceName(ENUM_CALENDAR_EVENT_IMPORTANCE i)
  {
   if(i == CALENDAR_IMPORTANCE_HIGH)     return "high";
   if(i == CALENDAR_IMPORTANCE_MODERATE) return "moderate";
   if(i == CALENDAR_IMPORTANCE_LOW)      return "low";
   return "none";
  }

string ImpactName(ENUM_CALENDAR_EVENT_IMPACT i)
  {
   if(i == CALENDAR_IMPACT_POSITIVE) return "positive";
   if(i == CALENDAR_IMPACT_NEGATIVE) return "negative";
   return "na";
  }

string Num(MqlCalendarValue &v, int which)
  {
   // which: 0 actual, 1 forecast, 2 previous, 3 revised previous; empty when the value is missing
   bool has = (which == 0 ? v.HasActualValue() : which == 1 ? v.HasForecastValue()
               : which == 2 ? v.HasPreviousValue() : v.HasRevisedValue());
   if(!has) return "";
   double x = (which == 0 ? v.GetActualValue() : which == 1 ? v.GetForecastValue()
               : which == 2 ? v.GetPreviousValue() : v.GetRevisedValue());
   return DoubleToString(x, 6);
  }

void OnStart()
  {
   datetime to = (InpTo == 0 ? TimeTradeServer() + 7 * 86400 : InpTo);
   int fh = FileOpen(InpFile, FILE_WRITE | FILE_CSV | FILE_ANSI | FILE_COMMON, ',');
   if(fh == INVALID_HANDLE)
     {
      Print("ExportCalendar: cannot open ", InpFile, " error ", GetLastError());
      return;
     }
   // time is trade-server time; server_utc_offset_s lets the reader convert it to UTC
   FileWrite(fh, "time_server", "server_utc_offset_s", "currency", "event_id", "event", "importance", "sector",
             "actual", "forecast", "previous", "revised_previous", "impact");
   long offset = (long)(TimeTradeServer() - TimeGMT());
   string cur[];
   int n = StringSplit(InpCurrencies, ',', cur);
   int rows = 0;
   for(int k = 0; k < n; k++)
     {
      MqlCalendarValue vals[];
      // year by year: one call over 15 years can hit the terminal's limits
      for(datetime a = InpFrom; a < to; a += 365 * 86400)
        {
         datetime b = MathMin(a + 365 * 86400, to);
         ArrayFree(vals);
         if(CalendarValueHistory(vals, a, b, NULL, cur[k]) <= 0)
            continue;
         for(int i = 0; i < ArraySize(vals); i++)
           {
            MqlCalendarEvent ev;
            if(!CalendarEventById(vals[i].event_id, ev))
               continue;
            if(InpOnlyMedHigh && ev.importance != CALENDAR_IMPORTANCE_HIGH && ev.importance != CALENDAR_IMPORTANCE_MODERATE)
               continue;
            string name = ev.name;
            StringReplace(name, ",", " ");
            FileWrite(fh, TimeToString(vals[i].time, TIME_DATE | TIME_MINUTES), offset, cur[k], (long)ev.id, name,
                      ImportanceName(ev.importance), (int)ev.sector, Num(vals[i], 0), Num(vals[i], 1), Num(vals[i], 2),
                      Num(vals[i], 3), ImpactName(vals[i].impact_type));
            rows++;
           }
        }
     }
   FileClose(fh);
   PrintFormat("ExportCalendar: %d rows written to Common\\Files\\%s", rows, InpFile);
  }
//+------------------------------------------------------------------+
