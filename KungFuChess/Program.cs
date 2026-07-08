using System;

namespace KungFuChess;

public static class Program
{
    public static int Main(string[] args)
    {
        try
        {
            var reader = new BoardReader(Console.In);
            var rows = reader.ReadBoard();

            var validator = new BoardValidator();
            validator.Validate(rows);

            var board = new Board(rows);
            var formatter = new BoardFormatter();
            Console.Write(formatter.Format(board));
            return 0;
        }
        catch (InvalidBoardException)
        {
            return 1;
        }
    }
}
